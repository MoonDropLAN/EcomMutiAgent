const sessionId = "demo-session";
const messageInput = document.getElementById("message");
const messages = document.getElementById("messages");
const products = document.getElementById("products");
const productCount = document.getElementById("productCount");
const coupon = document.getElementById("coupon");
const order = document.getElementById("order");
const trace = document.getElementById("trace");
const intentBadge = document.getElementById("intentBadge");
const sendButton = document.getElementById("send");
const uiState = { products: [], couponPlan: null, order: null, traceSteps: [] };

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `¥${Number(value).toLocaleString("zh-CN")}`;
}

function appendMessage(role, text) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.textContent = text;
  messages.appendChild(node);
  messages.scrollTop = messages.scrollHeight;
}

function setEmpty(node, text) {
  node.className = `${node.className.split(" ")[0]} empty-state`;
  node.textContent = text;
}

function renderProducts(items = []) {
  productCount.textContent = String(items.length);
  if (!items.length) {
    setEmpty(products, "等待导购结果");
    return;
  }
  products.className = "product-grid";
  products.innerHTML = items
    .map((item) => {
      const tags = (item.tags || []).slice(0, 3).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("");
      const stock = item.stock ? `${item.stock.available_stock} 可售 / ${item.stock.locked_stock} 锁定` : "库存待查";
      const specs = Object.entries(item.specs || {}).slice(0, 3)
        .map(([key, value]) => `<li><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></li>`)
        .join("");
      return `
        <article class="product-card">
          <div class="product-card-top">
            <div>
              <h3>${escapeHtml(item.name)}</h3>
              <p>${escapeHtml(item.brand)} · ${escapeHtml(item.category)}</p>
            </div>
            <strong>${money(item.base_price)}</strong>
          </div>
          <div class="tag-row">${tags}</div>
          <ul class="spec-list">${specs}</ul>
          <div class="stock-line">${escapeHtml(stock)}</div>
        </article>`;
    })
    .join("");
}

function renderCoupon(plan) {
  if (!plan || !plan.best_plan) {
    setEmpty(coupon, "等待优惠计算");
    return;
  }
  coupon.className = "coupon-box";
  const best = plan.best_plan;
  const eligible = (plan.eligible_coupons || []).map((item) => `<span>${escapeHtml(item.coupon_id)}</span>`).join("");
  const ineligible = (plan.ineligible_coupons || []).slice(0, 3)
    .map((item) => `<li>${escapeHtml(item.coupon_id)}：${escapeHtml(item.reason)}</li>`)
    .join("");
  coupon.innerHTML = `
    <div class="price-row">
      <div><span>原价</span><strong>${money(plan.total_amount)}</strong></div>
      <div><span>优惠</span><strong>-${money(best.discount_amount).replace("¥", "")}</strong></div>
      <div class="payable"><span>应付</span><strong>${money(best.payable_amount)}</strong></div>
    </div>
    <div class="coupon-tags">${eligible || "暂无可用券"}</div>
    <p>${escapeHtml(best.explanation || "已计算最优优惠方案")}</p>
    ${ineligible ? `<ul class="muted-list">${ineligible}</ul>` : ""}`;
}

function renderOrder(orderData) {
  if (!orderData) {
    setEmpty(order, "尚未创建订单");
    return;
  }
  order.className = "order-box";
  const items = (orderData.items || []).map((item) => `<li>${escapeHtml(item.product_id)} × ${escapeHtml(item.quantity)}</li>`).join("");
  order.innerHTML = `
    <div class="order-head">
      <div>
        <span>订单号</span>
        <strong>${escapeHtml(orderData.id)}</strong>
      </div>
      <mark class="status ${escapeHtml(orderData.status)}">${escapeHtml(orderData.status)}</mark>
    </div>
    <div class="order-amounts">
      <span>总额 ${money(orderData.total_amount)}</span>
      <span>优惠 ${money(orderData.discount_amount)}</span>
      <strong>应付 ${money(orderData.payable_amount)}</strong>
    </div>
    <ul class="muted-list">${items}</ul>`;
}

function renderTrace(steps = []) {
  if (!steps.length) {
    trace.className = "trace-list empty-state";
    trace.textContent = "等待工具调用";
    return;
  }
  trace.className = "trace-list";
  trace.innerHTML = steps
    .map((step, index) => `
      <li>
        <span>${index + 1}</span>
        <div>
          <strong>${escapeHtml(step.agent_name)}</strong>
          <p>${escapeHtml(step.decision_reason || step.intent || "")}</p>
          ${step.tool_name ? `<code>${escapeHtml(step.tool_name)}</code>` : ""}
        </div>
      </li>`)
    .join("");
}

function renderState(data) {
  intentBadge.textContent = data.intent || "general";
  if (Array.isArray(data.recommended_products) && data.recommended_products.length) {
    uiState.products = data.recommended_products;
  }
  if (data.coupon_plan) {
    uiState.couponPlan = data.coupon_plan;
  }
  if (data.order) {
    uiState.order = data.order;
  }
  if (Array.isArray(data.trace_steps)) {
    uiState.traceSteps = data.trace_steps;
  }
  renderProducts(uiState.products);
  renderCoupon(uiState.couponPlan);
  renderOrder(uiState.order);
  renderTrace(uiState.traceSteps);
}

async function sendMessage(prompt) {
  const message = prompt || messageInput.value.trim();
  if (!message) return;
  appendMessage("user", message);
  sendButton.disabled = true;
  sendButton.textContent = "处理中";
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    const data = await response.json();
    appendMessage("assistant", data.final_answer || "没有返回内容");
    renderState(data);
  } catch (error) {
    appendMessage("assistant", "请求失败，请检查服务是否启动。");
  } finally {
    sendButton.disabled = false;
    sendButton.textContent = "发送";
  }
}

document.getElementById("send").addEventListener("click", () => sendMessage());
messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) sendMessage();
});
document.querySelectorAll("button[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});
