document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page || "home";
  const stateEl = document.getElementById("initial-state");
  const wishlistGridHome = document.getElementById("wishlist-grid");
  const wishlistGridPage = document.getElementById("wishlist-page-grid");
  const postsGrid = document.getElementById("posts-grid");
  const wishForm = document.getElementById("wish-form");
  const wishCreateForm = document.getElementById("wish-create-form");
  const postForm = document.getElementById("post-form");
  const adminTokenInput = document.getElementById("admin-token");
  const saveTokenBtn = document.getElementById("save-token");
  const filterChips = document.querySelectorAll(".filter-chip");

  const toast = (() => {
    const node = document.createElement("div");
    node.className = "toast";
    document.body.appendChild(node);
    let timer;
    return (text, tone = "info") => {
      node.textContent = text;
      node.dataset.tone = tone;
      node.style.opacity = "1";
      clearTimeout(timer);
      timer = setTimeout(() => (node.style.opacity = "0"), 2800);
    };
  })();

  let adminToken = localStorage.getItem("resume_admin_token") || "";
  if (adminToken && adminTokenInput) {
    adminTokenInput.value = adminToken;
  }

  const initialState = stateEl ? JSON.parse(stateEl.textContent) : { wishlist: [], posts: [] };
  const state = {
    wishlist: initialState.wishlist || [],
    posts: initialState.posts || [],
    filter: "all",
  };

  const api = async (path, { method = "GET", body, admin = false } = {}) => {
    const headers = {};
    adminToken = adminTokenInput?.value || adminToken || "";
    if (admin && adminToken) {
      headers["X-Admin-Token"] = adminToken;
    }
    const options = {
      method,
      headers,
      body: undefined,
    };
    if (body instanceof FormData) {
      options.body = body;
    } else if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    if (!response.ok) {
      let detail = "Ошибка запроса";
      try {
        const data = await response.json();
        detail = data.detail || JSON.stringify(data);
      } catch {
        detail = response.statusText;
      }
      throw new Error(detail);
    }
    return response.json();
  };

  const filteredWishlist = () => {
    const filter = state.filter || "all";
    if (filter === "free") return state.wishlist.filter((w) => !w.reserved);
    if (filter === "reserved") return state.wishlist.filter((w) => w.reserved);
    return state.wishlist;
  };

  const renderWishlistTo = (grid, options = {}) => {
    if (!grid) return;
    const items = options.items || filteredWishlist();
    const isAdmin = !!(adminTokenInput?.value || adminToken);

    if (!items.length) {
      grid.innerHTML = `<div class="card"><div class="card-title">Пока пусто</div><p class="muted">Добавьте идеи через админку.</p></div>`;
      return;
    }

    grid.innerHTML = items
      .map((item) => {
        const reserved = item.reserved;
        const adminPart = isAdmin && options.adminInline
          ? `
            <div class="wish-admin" data-admin="true">
              <div class="small">Быстрые правки (токен нужен)</div>
              <input data-field="title" placeholder="Заголовок" value="${item.title || ""}">
              <input data-field="price" placeholder="Цена/ориентир" value="${item.price || ""}">
              <input data-field="link" placeholder="Ссылка" value="${item.link || ""}">
              <textarea data-field="description" placeholder="Описание">${item.description || ""}</textarea>
              <input data-field="image" type="file" accept="image/*">
              <div class="wish-actions">
                <button class="button ghost" data-action="update" data-id="${item.id}">Сохранить</button>
                <button class="button ghost" data-action="release" data-id="${item.id}">Снять бронь</button>
                <button class="button ghost" data-action="delete" data-id="${item.id}">Удалить</button>
              </div>
            </div>
          `
          : "";
        return `
        <div class="card wish-card" data-id="${item.id}">
          ${item.image_url ? `<div class="wish-cover" style="background-image:url('${item.image_url}')"></div>` : ""}
          <div class="badge ${reserved ? "busy" : "free"}">${reserved ? "Забронировано" : "Свободно"}</div>
          <div class="card-title">${item.title}</div>
          ${item.price ? `<p class="muted">Ориентир: ${item.price}</p>` : ""}
          ${item.description ? `<p class="muted">${item.description}</p>` : ""}
          ${item.link ? `<a class="chip" href="${item.link}" target="_blank">Ссылка</a>` : ""}
          ${
            reserved
              ? `<p class="small">Бронь: ${item.reserved_by || "—"}${item.reserved_contact ? " · " + item.reserved_contact : ""}${
                  item.reserved_note ? " · " + item.reserved_note : ""
                }</p>`
              : ""
          }
          <div class="form-inline">
            <input name="name" placeholder="Ваше имя" ${reserved ? "disabled" : ""}>
            <input name="contact" placeholder="Телеграм/телефон" ${reserved ? "disabled" : ""}>
            <input name="note" placeholder="Комментарий" ${reserved ? "disabled" : ""}>
            <button class="button full" data-action="reserve" data-id="${item.id}" ${reserved ? "disabled" : ""}>Забронировать</button>
          </div>
          <div class="wish-actions">
            ${
              reserved && isAdmin
                ? `<button class="button ghost full" data-action="release" data-id="${item.id}">Снять бронь (админ)</button>`
                : ""
            }
            ${
              isAdmin && !options.adminInline
                ? `<button class="button ghost full" data-action="delete" data-id="${item.id}">Удалить (админ)</button>`
                : ""
            }
          </div>
          ${adminPart}
        </div>
      `;
      })
      .join("");
  };

  const renderWishlist = () => {
    const items = filteredWishlist();
    if (wishlistGridHome) {
      const preview = items.slice(0, 4);
      renderWishlistTo(wishlistGridHome, { items: preview });
    }
    if (wishlistGridPage) {
      renderWishlistTo(wishlistGridPage, { items, adminInline: true });
    }
  };

  const renderPosts = () => {
    if (!postsGrid) return;
    if (!state.posts.length) {
      postsGrid.innerHTML = `<div class="card"><div class="card-title">Нет записей</div><p class="muted">Добавьте первую заметку в админке.</p></div>`;
      return;
    }
    postsGrid.innerHTML = state.posts
      .map(
        (post) => `
      <div class="card">
        <div class="card-title">${post.title}</div>
        <p class="muted">${post.summary}</p>
        <p>${post.body}</p>
        ${
          post.tags?.length
            ? `<div>${post.tags.map((t) => `<span class="tag">${t}</span>`).join("")}</div>`
            : ""
        }
      </div>
    `,
      )
      .join("");
  };

  const refreshAll = async () => {
    try {
      const data = await api("/api/resume");
      state.wishlist = data.wishlist || [];
      state.posts = data.posts || [];
      renderWishlist();
      renderPosts();
    } catch (err) {
      toast(err.message || "Не удалось обновить данные", "error");
    }
  };

  if (saveTokenBtn && adminTokenInput) {
    saveTokenBtn.addEventListener("click", () => {
      adminToken = adminTokenInput.value.trim();
      localStorage.setItem("resume_admin_token", adminToken);
      renderWishlist();
      toast("Токен сохранён в браузере");
    });
  }

  if (filterChips.length) {
    filterChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        filterChips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        state.filter = chip.dataset.filter || "all";
        renderWishlist();
      });
    });
    filterChips[0]?.classList.add("active");
  }

  if (wishForm) {
    wishForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(wishForm);
      const payload = {
        title: formData.get("title"),
        price: formData.get("price"),
        link: formData.get("link"),
        description: formData.get("description"),
      };
      try {
        const { item } = await api("/api/wishlist", { method: "POST", body: payload, admin: true });
        state.wishlist.unshift(item);
        renderWishlist();
        wishForm.reset();
        toast("Пункт добавлен");
      } catch (err) {
        toast(err.message || "Не удалось создать", "error");
      }
    });
  }

  if (wishCreateForm) {
    wishCreateForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(wishCreateForm);
      try {
        const { item } = await api("/api/wishlist", { method: "POST", body: formData, admin: true });
        state.wishlist.unshift(item);
        renderWishlist();
        wishCreateForm.reset();
        toast("Подарок добавлен");
      } catch (err) {
        toast(err.message || "Не удалось добавить подарок", "error");
      }
    });
  }

  if (postForm) {
    postForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(postForm);
      const payload = {
        title: formData.get("title"),
        summary: formData.get("summary"),
        body: formData.get("body"),
        tags: (formData.get("tags") || "")
          .toString()
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      };
      try {
        const { item } = await api("/api/posts", { method: "POST", body: payload, admin: true });
        state.posts.unshift(item);
        renderPosts();
        postForm.reset();
        toast("Пост опубликован");
      } catch (err) {
        toast(err.message || "Не удалось опубликовать", "error");
      }
    });
  }

  const wishClickHandler = async (grid, e) => {
    const target = e.target.closest("[data-action]");
    if (!target) return;
    const action = target.dataset.action;
    const id = target.dataset.id;
    if (!id) return;
    const card = target.closest(".wish-card");

    if (action === "reserve") {
      const nameInput = card?.querySelector('input[name="name"]');
      const contactInput = card?.querySelector('input[name="contact"]');
      const noteInput = card?.querySelector('input[name="note"]');
      const payload = {
        name: nameInput?.value,
        contact: contactInput?.value,
        note: noteInput?.value,
      };
      if (!payload.name) {
        toast("Укажите имя для брони", "error");
        return;
      }
      try {
        const { item } = await api(`/api/wishlist/${id}/reserve`, { method: "POST", body: payload });
        const idx = state.wishlist.findIndex((w) => w.id === item.id);
        if (idx >= 0) state.wishlist[idx] = item;
        renderWishlist();
        toast("Бронь сохранена");
      } catch (err) {
        toast(err.message || "Не удалось забронировать", "error");
      }
    }

    if (action === "release") {
      try {
        const { item } = await api(`/api/wishlist/${id}/release`, { method: "POST", admin: true });
        const idx = state.wishlist.findIndex((w) => w.id === item.id);
        if (idx >= 0) state.wishlist[idx] = item;
        renderWishlist();
        toast("Бронь снята");
      } catch (err) {
        toast(err.message || "Нужен токен админа", "error");
      }
    }

    if (action === "delete") {
      if (!confirm("Удалить пункт?")) return;
      try {
        await api(`/api/wishlist/${id}`, { method: "DELETE", admin: true });
        state.wishlist = state.wishlist.filter((w) => String(w.id) !== String(id));
        renderWishlist();
        toast("Удалено");
      } catch (err) {
        toast(err.message || "Не удалось удалить", "error");
      }
    }

    if (action === "update") {
      if (!adminTokenInput?.value) {
        toast("Нужен токен", "error");
        return;
      }
      const adminArea = target.closest(".wish-admin");
      if (!adminArea) return;
      const fd = new FormData();
      adminArea.querySelectorAll("[data-field]").forEach((field) => {
        const name = field.dataset.field;
        if (!name) return;
        if (field.type === "file") {
          if (field.files?.[0]) fd.append("image", field.files[0]);
        } else {
          fd.append(name, field.value);
        }
      });
      try {
        const { item } = await api(`/api/wishlist/${id}`, { method: "PUT", body: fd, admin: true });
        const idx = state.wishlist.findIndex((w) => w.id === item.id);
        if (idx >= 0) state.wishlist[idx] = item;
        renderWishlist();
        toast("Карточка обновлена");
      } catch (err) {
        toast(err.message || "Не удалось обновить", "error");
      }
    }
  };

  if (wishlistGridHome) {
    wishlistGridHome.addEventListener("click", (e) => wishClickHandler(wishlistGridHome, e));
  }
  if (wishlistGridPage) {
    wishlistGridPage.addEventListener("click", (e) => wishClickHandler(wishlistGridPage, e));
  }

  renderWishlist();
  renderPosts();
  // периодическая подгрузка чтобы видеть новые брони/посты без перезапуска
  setInterval(() => refreshAll(), 60000);
});
