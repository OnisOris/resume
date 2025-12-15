from __future__ import annotations

import json
import secrets
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from fastapi.encoders import jsonable_encoder

from .config import Settings, get_settings
from .database import create_db_and_tables, ensure_wishlist_columns, init_engine
from .deps import get_db_session, require_admin
from .models import Post, WishItem
from .resume_loader import ResumeLoader
from .schemas import (
    PostCreate,
    PostPublic,
    PostUpdate,
    WishItemCreate,
    WishItemPublic,
    WishItemReserve,
    WishItemUpdate,
)
from .utils import tags_from_text, tags_to_text


def _templates() -> Jinja2Templates:
    template_dir = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(template_dir))
    return templates


def wish_to_public(item: WishItem, data_prefix: str = "/data") -> WishItemPublic:
    return WishItemPublic(
        id=item.id or 0,
        title=item.title,
        description=item.description,
        link=item.link,
        price=item.price,
        reserved=item.reserved_by is not None,
        reserved_by=item.reserved_by,
        reserved_contact=item.reserved_contact,
        reserved_note=item.reserved_note,
        reserved_at=item.reserved_at,
        image_url=f"{data_prefix}/{item.image_path}" if item.image_path else None,
    )


def post_to_public(post: Post) -> PostPublic:
    return PostPublic(
        id=post.id or 0,
        title=post.title,
        summary=post.summary,
        body=post.body,
        tags=tags_from_text(post.tags),
        created_at=post.created_at,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    init_engine(settings.resolved_database_url, settings)
    create_db_and_tables()
    ensure_wishlist_columns()

    app = FastAPI(title=settings.site_name, description=settings.site_tagline)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_dir = Path(__file__).parent / "static"
    data_dir = settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

    templates = _templates()
    resume_loader = ResumeLoader(data_dir / "resume.yaml")

    @app.middleware("http")
    async def add_state(request, call_next):  # type: ignore[no-untyped-def]
        request.state.settings = settings
        return await call_next(request)

    def _build_wishlist(session: Session) -> List[Dict[str, Any]]:
        items = session.exec(select(WishItem).order_by(WishItem.created_at.desc())).all()
        return [wish_to_public(i).model_dump() for i in items]

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, session: Session = Depends(get_db_session)) -> HTMLResponse:
        resume_data: Dict[str, Any] = resume_loader.load()
        wishlist_items = _build_wishlist(session)
        posts = session.exec(select(Post).order_by(Post.created_at.desc())).all()

        initial_state = {
            "resume": resume_data,
            "wishlist": wishlist_items,
            "posts": [post_to_public(p).model_dump() for p in posts],
        }
        initial_json = json.dumps(jsonable_encoder(initial_state), ensure_ascii=False, indent=2)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "settings": settings,
                "resume": resume_data,
                "initial_json": initial_json,
                "page_name": "home",
            },
        )

    @app.get("/wishlist", response_class=HTMLResponse)
    def wishlist_page(request: Request, session: Session = Depends(get_db_session)) -> HTMLResponse:
        resume_data: Dict[str, Any] = resume_loader.load()
        wishlist_items = _build_wishlist(session)
        initial_state = {
            "resume": resume_data,
            "wishlist": wishlist_items,
        }
        initial_json = json.dumps(jsonable_encoder(initial_state), ensure_ascii=False, indent=2)
        return templates.TemplateResponse(
            "wishlist.html",
            {
                "request": request,
                "settings": settings,
                "resume": resume_data,
                "initial_json": initial_json,
                "page_name": "wishlist",
            },
        )

    @app.get("/api/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/resume")
    def api_resume(session: Session = Depends(get_db_session)) -> Dict[str, Any]:
        wishlist_items = _build_wishlist(session)
        posts = session.exec(select(Post).order_by(Post.created_at.desc())).all()
        return {
            "resume": resume_loader.load(),
            "wishlist": wishlist_items,
            "posts": [post_to_public(p).model_dump() for p in posts],
        }

    @app.get("/api/wishlist")
    def list_wishlist(session: Session = Depends(get_db_session)) -> Dict[str, List[Dict[str, Any]]]:
        items = session.exec(select(WishItem).order_by(WishItem.created_at.desc())).all()
        return {"items": [wish_to_public(i).model_dump() for i in items]}

    def _store_image(upload: UploadFile | None, base_dir: Path) -> str | None:
        if not upload or not upload.filename:
            return None
        if not upload.content_type or not upload.content_type.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нужно изображение")
        ext = Path(upload.filename).suffix.lower() or ".jpg"
        safe_name = f"{secrets.token_hex(4)}{ext}"
        target_dir = base_dir / "wishlist"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / safe_name
        with target_path.open("wb") as f:
            shutil.copyfileobj(upload.file, f)
        return f"wishlist/{safe_name}"

    @app.post("/api/wishlist", dependencies=[Depends(require_admin)])
    async def create_wish(
        request: Request,
        title: str | None = Form(None),
        description: str | None = Form(None),
        link: str | None = Form(None),
        price: str | None = Form(None),
        image: UploadFile | None = File(None),
        session: Session = Depends(get_db_session),
    ) -> Dict[str, Any]:
        data: Dict[str, Any]
        if title is None and request.headers.get("content-type", "").startswith("application/json"):
            raw = await request.json()
            data = WishItemCreate.model_validate(raw).model_dump(exclude_none=True)
        else:
            data = {
                "title": title,
                "description": description,
                "link": link,
                "price": price,
            }
        if not data.get("title"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Нужен заголовок")
        image_path = _store_image(image, data_dir)
        if image_path:
            data["image_path"] = image_path
        item = WishItem(**data)
        session.add(item)
        session.commit()
        session.refresh(item)
        return {"status": "ok", "item": wish_to_public(item).model_dump()}

    @app.put("/api/wishlist/{item_id}", dependencies=[Depends(require_admin)])
    async def update_wish(
        item_id: int,
        request: Request,
        title: str | None = Form(None),
        description: str | None = Form(None),
        link: str | None = Form(None),
        price: str | None = Form(None),
        image: UploadFile | None = File(None),
        session: Session = Depends(get_db_session),
    ) -> Dict[str, Any]:
        item = session.get(WishItem, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент не найден")
        data: Dict[str, Any]
        if title is None and request.headers.get("content-type", "").startswith("application/json"):
            raw = await request.json()
            data = WishItemUpdate.model_validate(raw).model_dump(exclude_none=True)
        else:
            data = {k: v for k, v in {"title": title, "description": description, "link": link, "price": price}.items() if v}
        if image and image.filename:
            data["image_path"] = _store_image(image, data_dir)
        for field, value in data.items():
            setattr(item, field, value)
        session.add(item)
        session.commit()
        session.refresh(item)
        return {"status": "ok", "item": wish_to_public(item).model_dump()}

    @app.delete("/api/wishlist/{item_id}", dependencies=[Depends(require_admin)])
    def delete_wish(item_id: int, session: Session = Depends(get_db_session)) -> Dict[str, Any]:
        item = session.get(WishItem, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент не найден")
        session.delete(item)
        session.commit()
        return {"status": "ok"}

    @app.post("/api/wishlist/{item_id}/reserve")
    def reserve_wish(
        item_id: int, payload: WishItemReserve, session: Session = Depends(get_db_session)
    ) -> Dict[str, Any]:
        item = session.get(WishItem, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент не найден")
        if item.reserved_by:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Уже забронировано")
        item.reserved_by = payload.name.strip()
        item.reserved_contact = payload.contact
        item.reserved_note = payload.note
        item.reserved_at = datetime.utcnow()
        session.add(item)
        session.commit()
        session.refresh(item)
        return {"status": "ok", "item": wish_to_public(item).model_dump()}

    @app.post("/api/wishlist/{item_id}/release", dependencies=[Depends(require_admin)])
    def release_wish(item_id: int, session: Session = Depends(get_db_session)) -> Dict[str, Any]:
        item = session.get(WishItem, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент не найден")
        item.reserved_by = None
        item.reserved_contact = None
        item.reserved_note = None
        item.reserved_at = None
        session.add(item)
        session.commit()
        session.refresh(item)
        return {"status": "ok", "item": wish_to_public(item).model_dump()}

    @app.get("/api/posts")
    def list_posts(session: Session = Depends(get_db_session)) -> Dict[str, List[Dict[str, Any]]]:
        posts = session.exec(select(Post).order_by(Post.created_at.desc())).all()
        return {"items": [post_to_public(p).model_dump() for p in posts]}

    @app.post("/api/posts", dependencies=[Depends(require_admin)])
    def create_post(payload: PostCreate, session: Session = Depends(get_db_session)) -> Dict[str, Any]:
        post = Post(**payload.model_dump(exclude_none=True))
        post.tags = tags_to_text(payload.tags)
        session.add(post)
        session.commit()
        session.refresh(post)
        return {"status": "ok", "item": post_to_public(post).model_dump()}

    @app.put("/api/posts/{post_id}", dependencies=[Depends(require_admin)])
    def update_post(
        post_id: int, payload: PostUpdate, session: Session = Depends(get_db_session)
    ) -> Dict[str, Any]:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пост не найден")
        data = payload.model_dump(exclude_none=True)
        tags = data.pop("tags", None)
        for field, value in data.items():
            setattr(post, field, value)
        if tags is not None:
            post.tags = tags_to_text(tags)
        session.add(post)
        session.commit()
        session.refresh(post)
        return {"status": "ok", "item": post_to_public(post).model_dump()}

    @app.delete("/api/posts/{post_id}", dependencies=[Depends(require_admin)])
    def delete_post(post_id: int, session: Session = Depends(get_db_session)) -> Dict[str, str]:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пост не найден")
        session.delete(post)
        session.commit()
        return {"status": "ok"}

    return app
