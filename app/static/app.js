const API_BASE = "/api";
let authToken = localStorage.getItem("authToken");

function apiHeaders(extra = {}) {
  const headers = { "Content-Type": "application/json", ...extra };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  return headers;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: apiHeaders(options.headers || {}),
  });

  if (response.status === 401) {
    localStorage.removeItem("authToken");
    window.location.href = "/login";
    return;
  }

  const data = await response.json();
  if (!response.ok) {
    const detail = data?.detail || "Ошибка";
    throw new Error(detail);
  }
  return data;
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

function renderProducts(products) {
  const grid = document.getElementById("productsGrid");
  if (!grid) return;
  grid.innerHTML = "";
  products.forEach((product) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="card-img" style="background-image:url('${product.image || "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=60"}')"></div>
      <div class="card-content">
        <div class="card-header">
          <h3>${product.title}</h3>
          <span class="pill">${(product.price / 100).toFixed(2)} ₽</span>
        </div>
        <p class="muted">${product.description || "Описание отсутствует"}</p>
        <button class="primary block" data-product="${product.id}">Добавить в корзину</button>
      </div>
    `;
    grid.appendChild(card);
  });

  grid.querySelectorAll("button[data-product]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!authToken) {
        window.location.href = "/login";
        return;
      }
      try {
        await apiRequest("/cart/add", {
          method: "POST",
          body: JSON.stringify({ product_id: Number(btn.dataset.product), quantity: 1 }),
        });
        showToast("Товар добавлен в корзину", "success");
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  });
}

async function loadProducts() {
  try {
    const products = await apiRequest("/products/");
    renderProducts(products);
  } catch (err) {
    console.error(err);
    showToast("Не удалось загрузить товары", "error");
  }
}

async function handleLoginForm() {
  const form = document.getElementById("loginForm");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      const res = await apiRequest("/auth/login-json", {
        method: "POST",
        body: JSON.stringify(data),
      });
      authToken = res.access_token;
      localStorage.setItem("authToken", authToken);
      window.location.href = "/";
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

async function handleRegisterForm() {
  const form = document.getElementById("registerForm");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      await apiRequest("/auth/register", { method: "POST", body: JSON.stringify(data) });
      showToast("Регистрация завершена, выполните вход", "success");
      window.location.href = "/login";
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

async function loadCart() {
  const cartContainer = document.getElementById("cartItems");
  const summaryContainer = document.getElementById("cartSummary");
  if (!cartContainer) return;
  try {
    const cart = await apiRequest("/cart/");
    cartContainer.innerHTML = "";
    cart.items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "cart-row";
      row.innerHTML = `
        <div>
          <div class="fw-bold">${item.product.title}</div>
          <div class="muted">${(item.product.price / 100).toFixed(2)} ₽</div>
        </div>
        <div class="cart-controls">
          <input type="number" min="1" value="${item.quantity}" data-id="${item.id}">
          <button class="ghost" data-remove="${item.id}">✕</button>
        </div>
      `;
      cartContainer.appendChild(row);
    });

    const total = cart.subtotal / 100;
    summaryContainer.innerHTML = `
      <div class="summary-line"><span>Подытог</span><span>${total.toFixed(2)} ₽</span></div>
      <div class="summary-line"><span>Скидка</span><span>- ${(cart.discount / 100).toFixed(2)} ₽</span></div>
      <div class="summary-line total"><span>Итого</span><span>${(cart.total / 100).toFixed(2)} ₽</span></div>
      <button id="checkoutBtn" class="primary block mt">Оформить заказ</button>
    `;

    cartContainer.querySelectorAll("input[type=number]").forEach((input) => {
      input.addEventListener("change", async () => {
        try {
          await apiRequest(`/cart/item/${input.dataset.id}`, {
            method: "PUT",
            body: JSON.stringify({ product_id: 0, quantity: Number(input.value) }),
          });
          loadCart();
        } catch (err) {
          showToast(err.message, "error");
        }
      });
    });

    cartContainer.querySelectorAll("button[data-remove]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await apiRequest(`/cart/item/${btn.dataset.remove}`, { method: "DELETE" });
        loadCart();
      });
    });

    document.getElementById("checkoutBtn")?.addEventListener("click", handleCheckout);
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleCheckout() {
  const couponCode = document.getElementById("couponCode")?.value || null;
  const billingEmail = document.getElementById("billingEmail")?.value || null;
  try {
    const order = await apiRequest("/orders/", {
      method: "POST",
      body: JSON.stringify({ coupon_code: couponCode, billing_email: billingEmail }),
    });
    showToast("Заказ создан", "success");
    if (order.lab_flag) {
      alert(`Лабораторный флаг: ${order.lab_flag}`);
    }
    loadCart();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function loadOrders() {
  const container = document.getElementById("ordersList");
  if (!container) return;
  try {
    const orders = await apiRequest("/orders/");
    container.innerHTML = "";
    orders.forEach((order) => {
      const card = document.createElement("div");
      card.className = "card";
      card.innerHTML = `
        <div class="card-header">
          <div>
            <div class="fw-bold">Заказ #${order.id}</div>
            <div class="muted">${new Date(order.created_at).toLocaleString()}</div>
          </div>
          <span class="pill">${order.status}</span>
        </div>
        <div class="muted">Купон: ${order.coupon_code || "—"}</div>
        <div class="muted">Скидка: ${(order.discount_applied / 100).toFixed(2)} ₽</div>
        <div class="muted">Итого: ${(order.total_amount / 100).toFixed(2)} ₽</div>
        ${order.lab_flag ? `<div class="flag">Флаг: ${order.lab_flag}</div>` : ""}
      `;
      container.appendChild(card);
    });
  } catch (err) {
    showToast("Не удалось загрузить заказы", "error");
  }
}

async function loadAdmin() {
  const adminList = document.getElementById("adminOrders");
  if (!adminList) return;
  try {
    const orders = await apiRequest("/orders/admin");
    adminList.innerHTML = "";
    orders.forEach((order) => {
      const row = document.createElement("div");
      row.className = "card";
      row.innerHTML = `
        <div class="card-header">
          <div>
            <div class="fw-bold">Заказ #${order.id}</div>
            <div class="muted">${order.billing_email || "не указано"}</div>
          </div>
          <span class="pill">${order.status}</span>
        </div>
        <div class="muted">${(order.total_amount / 100).toFixed(2)} ₽ / скидка ${(order.discount_applied / 100).toFixed(2)} ₽</div>
        ${order.lab_flag ? `<div class="flag">Флаг: ${order.lab_flag}</div>` : ""}
        <div class="status-change">
          <input data-id="${order.id}" placeholder="from_status -> to_status" />
          <button data-change="${order.id}" class="ghost">Применить</button>
        </div>
      `;
      adminList.appendChild(row);
    });

    adminList.querySelectorAll("button[data-change]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const input = adminList.querySelector(`input[data-id="${btn.dataset.change}"]`);
        if (!input?.value.includes("->")) return;
        const [from_status, to_status] = input.value.split("->").map((v) => v.trim());
        try {
          const order = await apiRequest(`/orders/${btn.dataset.change}/status`, {
            method: "PATCH",
            body: JSON.stringify({ from_status, to_status }),
          });
          if (order.lab_flag) alert(`Лабораторный флаг: ${order.lab_flag}`);
          loadAdmin();
        } catch (err) {
          showToast(err.message, "error");
        }
      });
    });
  } catch (err) {
    showToast("Нет доступа или ошибка загрузки", "error");
  }
}

function bindLogout() {
  document.querySelectorAll("[data-logout]").forEach((btn) =>
    btn.addEventListener("click", () => {
      localStorage.removeItem("authToken");
      window.location.href = "/login";
    })
  );
}

document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname;
  bindLogout();
  if (path === "/") loadProducts();
  if (path === "/login") handleLoginForm();
  if (path === "/register") handleRegisterForm();
  if (path === "/cart") {
    if (!authToken) window.location.href = "/login";
    loadCart();
  }
  if (path === "/account") {
    if (!authToken) window.location.href = "/login";
    loadOrders();
  }
  if (path === "/admin") {
    if (!authToken) window.location.href = "/login";
    loadAdmin();
  }
});
