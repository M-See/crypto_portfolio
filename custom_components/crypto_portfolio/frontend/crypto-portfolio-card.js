(() => {
const ADVANCED_JSON_EDITOR_ROWS = 24;
const advancedJsonObservedRoots = new WeakSet();
const advancedJsonObservers = [];
let advancedJsonPatchScheduled = false;

function visitShadowDom(root, visitor) {
  for (const element of root.querySelectorAll("*")) {
    visitor(element);
    if (element.shadowRoot) {
      visitShadowDom(element.shadowRoot, visitor);
    }
  }
}

function patchAdvancedJsonEditor() {
  visitShadowDom(document, (element) => {
    const dataSchema = element.step?.data_schema;
    const isCryptoPortfolioJsonEditor =
      element.localName === "step-flow-form" &&
      element.step?.step_id === "advanced_json" &&
      Array.isArray(dataSchema) &&
      dataSchema.some((field) => field.name === "holdings_json");

    if (!isCryptoPortfolioJsonEditor) {
      return;
    }

    let parent = element;
    while (parent) {
      if (
        parent.localName === "ha-dialog" ||
        parent.localName === "ha-md-dialog" ||
        parent.localName === "ha-adaptive-dialog" ||
        parent.localName === "dialog-data-entry-flow"
      ) {
        parent.width = "large";
        parent.setAttribute("width", "large");
        parent.style.setProperty(
          "--ha-dialog-width-md",
          "min(1024px, calc(100vw - 32px))"
        );
        parent.style.setProperty(
          "--ha-dialog-max-width",
          "min(1100px, calc(100vw - 32px))"
        );
      }
      parent = parent.parentElement || parent.getRootNode()?.host;
    }

    visitShadowDom(element.shadowRoot || element, (editorElement) => {
      if (
        editorElement.localName === "ha-textarea" ||
        editorElement.localName === "ha-textfield" ||
        editorElement.localName === "textarea"
      ) {
        editorElement.rows = ADVANCED_JSON_EDITOR_ROWS;
        editorElement.resize = "vertical";
        editorElement.setAttribute("rows", String(ADVANCED_JSON_EDITOR_ROWS));
        editorElement.setAttribute("resize", "vertical");
        editorElement.style.width = "100%";
        editorElement.style.setProperty("--ha-textarea-max-height", "70vh");
      }
    });
  });
}

function scheduleAdvancedJsonEditorPatch() {
  if (advancedJsonPatchScheduled) {
    return;
  }

  advancedJsonPatchScheduled = true;
  window.requestAnimationFrame(() => {
    advancedJsonPatchScheduled = false;
    patchAdvancedJsonEditor();
    observeAdvancedJsonShadowRoots(document);
  });
}

function observeAdvancedJsonShadowRoots(root) {
  if (!advancedJsonObservedRoots.has(root)) {
    const observer = new MutationObserver(scheduleAdvancedJsonEditorPatch);
    observer.observe(root, { childList: true, subtree: true });
    advancedJsonObservedRoots.add(root);
    advancedJsonObservers.push(observer);
  }

  for (const element of root.querySelectorAll("*")) {
    if (element.shadowRoot) {
      observeAdvancedJsonShadowRoots(element.shadowRoot);
    }
  }
}

document.addEventListener("show-dialog", scheduleAdvancedJsonEditorPatch);
document.addEventListener("flow-update", scheduleAdvancedJsonEditorPatch);
window.setInterval(scheduleAdvancedJsonEditorPatch, 5000);
scheduleAdvancedJsonEditorPatch();

class CryptoPortfolioCard extends HTMLElement {
  static getStubConfig(hass) {
    return {
      entity: CryptoPortfolioCard.findPortfolioEntity(hass) || "sensor.crypto_portfolio_value",
      title: "Crypto Portfolio",
      sort_by: "profit",
      show_graph: true,
      history_hours: 168,
    };
  }

  static findPortfolioEntity(hass) {
    const states = hass?.states || {};
    const entity = Object.entries(states).find(([, state]) =>
      Array.isArray(state?.attributes?.positions)
    );
    return entity?.[0] || null;
  }

  setConfig(config) {
    this.config = {
      title: "Crypto Portfolio",
      sort_by: "value",
      show_graph: true,
      history_hours: 168,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 9;
  }

  getGridOptions() {
    return {
      columns: "full",
      min_columns: 6,
      rows: 8,
      min_rows: 5,
    };
  }

  render() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }

    const entityId =
      this.config.entity || CryptoPortfolioCard.findPortfolioEntity(this._hass);
    const state = this._hass?.states?.[entityId];
    if (!state) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="empty">Bitte einen Crypto-Portfolio-Sensor auswaehlen.</div>
        </ha-card>
        ${this.styles()}
      `;
      return;
    }

    const attrs = state.attributes || {};
    const positions = Array.isArray(attrs.positions) ? attrs.positions : [];
    const currency = state.attributes.unit_of_measurement || "EUR";
    const locale = this._hass?.locale?.language || navigator.language || "de-DE";
    const sortedPositions = this.sortPositions(positions);
    const profit = this.toNumber(attrs.profit);
    const profitPercent = this.toNumber(attrs.profit_percent);
    this.loadHistory(entityId);

    this.shadowRoot.innerHTML = `
      <ha-card>
        <div class="card">
          <div class="header">
            <div>
              <div class="title">${this.escape(this.config.title)}</div>
              <div class="subline">${positions.length} Positionen</div>
            </div>
            <div class="summary">
              <div class="summary-value">${this.formatMoney(state.state, currency, locale)}</div>
              <div class="${this.classForValue(profit)}">
                ${this.formatMoney(profit, currency, locale)}
                <span>${this.formatPercent(profitPercent, locale)}</span>
              </div>
            </div>
          </div>

          <div class="metrics">
            ${this.metric("Invest", this.formatMoney(attrs.invested, currency, locale))}
            ${this.metric("Wert", this.formatMoney(state.state, currency, locale))}
            ${this.metric("Gewinn", this.formatMoney(profit, currency, locale), this.classForValue(profit))}
          </div>

          ${this.config.show_graph === false ? "" : this.historyChart(state, currency, locale)}

          <div class="table">
            <div class="row head">
              <div>Coin</div>
              <div class="num price">Preis</div>
              <div class="num value">Wert</div>
              <div class="num invest">Invest</div>
              <div class="num gain">Gewinn</div>
              <div class="num percent">%</div>
            </div>
            ${sortedPositions.map((position) => this.positionRow(position, currency, locale)).join("")}
          </div>
        </div>
      </ha-card>
      ${this.styles()}
    `;
  }

  sortPositions(positions) {
    const key = this.config.sort_by;
    const sorted = [...positions];
    const valueFor = (position) => Math.abs(this.toNumber(position[key]) || 0);
    sorted.sort((left, right) => valueFor(right) - valueFor(left));
    return sorted;
  }

  positionRow(position, currency, locale) {
    const profit = this.toNumber(position.profit);
    const profitPercent = this.toNumber(position.profit_percent);
    const change = this.toNumber(position.change_24h_percent);
    return `
      <div class="row">
        <div class="coin">
          <div class="symbol">${this.escape(position.symbol || position.coin_id)}</div>
          <div class="amount">${this.formatAmount(position.amount, locale)}</div>
        </div>
        <div class="num price">${this.formatMoney(position.current_price, currency, locale)}</div>
        <div class="num value">${this.formatMoney(position.value, currency, locale)}</div>
        <div class="num invest">${this.formatMoney(position.invested, currency, locale)}</div>
        <div class="num gain ${this.classForValue(profit)}">${this.formatMoney(profit, currency, locale)}</div>
        <div class="num percent">
          <div class="${this.classForValue(profit)}">${this.formatPercent(profitPercent, locale)}</div>
          <div class="change ${this.classForValue(change)}">${this.formatPercent(change, locale)}</div>
        </div>
      </div>
    `;
  }

  loadHistory(entityId) {
    if (!entityId || !this._hass || typeof this._hass.callApi !== "function") {
      return;
    }

    const hours = Math.max(1, Number(this.config.history_hours) || 168);
    const cacheKey = `${entityId}:${hours}`;
    const now = Date.now();
    if (
      this._historyKey === cacheKey &&
      (this._historyLoading || (this._historyLoadedAt && now - this._historyLoadedAt < 300000))
    ) {
      return;
    }

    this._historyKey = cacheKey;
    this._historyLoading = true;
    this._historyError = null;
    const start = new Date(now - hours * 60 * 60 * 1000).toISOString();
    const end = new Date(now).toISOString();
    const params = new URLSearchParams({
      filter_entity_id: entityId,
      end_time: end,
      significant_changes_only: "0",
    });
    params.append("minimal_response", "");
    params.append("no_attributes", "");
    const path = `history/period/${encodeURIComponent(start)}?${params.toString()}`;

    this._hass
      .callApi("GET", path)
      .then((data) => {
        if (this._historyKey !== cacheKey) {
          return;
        }
        this._historyPoints = this.parseHistory(data);
        this._historyLoadedAt = Date.now();
        this._historyLoading = false;
        this.render();
      })
      .catch(() => {
        if (this._historyKey !== cacheKey) {
          return;
        }
        this._historyPoints = [];
        this._historyLoading = false;
        this._historyError = true;
        this.render();
      });
  }

  parseHistory(data) {
    const rows = Array.isArray(data?.[0]) ? data[0] : [];
    return rows
      .map((item, index) => {
        const value = this.toNumber(item.state ?? item.s);
        const rawTime =
          item.last_changed ?? item.last_updated ?? item.lc ?? item.lu ?? null;
        const timestamp =
          typeof rawTime === "number"
            ? rawTime * 1000
            : rawTime
              ? Date.parse(rawTime)
              : index;
        if (value === null || !Number.isFinite(timestamp)) {
          return null;
        }
        return { x: timestamp, y: value };
      })
      .filter(Boolean);
  }

  historyChart(state, currency, locale) {
    const currentValue = this.toNumber(state.state);
    const points = [...(this._historyPoints || [])];
    if (currentValue !== null) {
      points.push({ x: Date.now(), y: currentValue });
    }

    if (this._historyLoading && points.length < 2) {
      return `
        <div class="chart">
          <div class="chart-head">
            <div>
              <div class="chart-title">Portfolio Verlauf</div>
              <div class="subline">Lade Historie...</div>
            </div>
          </div>
          <div class="chart-placeholder"></div>
        </div>
      `;
    }

    if (this._historyError || points.length < 2) {
      return `
        <div class="chart">
          <div class="chart-head">
            <div>
              <div class="chart-title">Portfolio Verlauf</div>
              <div class="subline">Noch nicht genug Historie vorhanden</div>
            </div>
          </div>
          <div class="chart-placeholder"></div>
        </div>
      `;
    }

    const minY = Math.min(...points.map((point) => point.y));
    const maxY = Math.max(...points.map((point) => point.y));
    const minX = Math.min(...points.map((point) => point.x));
    const maxX = Math.max(...points.map((point) => point.x));
    const ySpan = maxY - minY || 1;
    const xSpan = maxX - minX || 1;
    const width = 100;
    const height = 48;
    const topPad = 4;
    const bottomPad = 4;
    const coords = points.map((point) => {
      const x = ((point.x - minX) / xSpan) * width;
      const y = topPad + (1 - (point.y - minY) / ySpan) * (height - topPad - bottomPad);
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    });
    const path = `M ${coords.join(" L ")}`;
    const area = `${path} L 100,${height} L 0,${height} Z`;
    const first = points[0].y;
    const last = points[points.length - 1].y;
    const trend = last - first;

    return `
      <div class="chart">
        <div class="chart-head">
          <div>
            <div class="chart-title">Portfolio Verlauf</div>
            <div class="subline">Letzte ${this.escape(this.config.history_hours)} Stunden</div>
          </div>
          <div class="chart-values">
            <div>${this.formatMoney(maxY, currency, locale)}</div>
            <div>${this.formatMoney(minY, currency, locale)}</div>
          </div>
        </div>
        <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
          <path class="chart-area ${this.classForValue(trend)}" d="${area}"></path>
          <path class="chart-line ${this.classForValue(trend)}" d="${path}"></path>
        </svg>
      </div>
    `;
  }

  metric(label, value, className = "") {
    return `
      <div class="metric">
        <div class="metric-label">${this.escape(label)}</div>
        <div class="metric-value ${className}">${this.escape(value)}</div>
      </div>
    `;
  }

  formatMoney(value, currency, locale) {
    const number = this.toNumber(value);
    if (number === null) {
      return "-";
    }
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      maximumFractionDigits: Math.abs(number) >= 100 ? 0 : 2,
    }).format(number);
  }

  formatPercent(value, locale) {
    const number = this.toNumber(value);
    if (number === null) {
      return "-";
    }
    return `${new Intl.NumberFormat(locale, {
      maximumFractionDigits: 2,
    }).format(number)}%`;
  }

  formatAmount(value, locale) {
    const number = this.toNumber(value);
    if (number === null) {
      return "-";
    }
    return new Intl.NumberFormat(locale, {
      maximumFractionDigits: 8,
    }).format(number);
  }

  classForValue(value) {
    const number = this.toNumber(value);
    if (number === null || number === 0) {
      return "neutral";
    }
    return number < 0 ? "negative" : "positive";
  }

  toNumber(value) {
    if (value === null || value === undefined || value === "unknown" || value === "unavailable") {
      return null;
    }
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  escape(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[char]);
  }

  styles() {
    return `
      <style>
        :host {
          display: block;
        }

        .card {
          padding: 16px;
        }

        .header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 14px;
        }

        .title {
          font-size: 20px;
          font-weight: 600;
          line-height: 1.2;
        }

        .subline,
        .amount,
        .change,
        .metric-label {
          color: var(--secondary-text-color);
          font-size: 12px;
          line-height: 1.35;
        }

        .summary {
          text-align: right;
          white-space: nowrap;
        }

        .summary-value {
          font-size: 22px;
          font-weight: 650;
          line-height: 1.15;
        }

        .summary span {
          margin-left: 6px;
          color: var(--secondary-text-color);
        }

        .metrics {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px;
          margin-bottom: 14px;
        }

        .metric {
          min-width: 0;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          padding: 10px;
          background: var(--card-background-color);
        }

        .metric-value {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          font-size: 15px;
          font-weight: 600;
        }

        .chart {
          margin-bottom: 14px;
          border-top: 1px solid var(--divider-color);
          padding-top: 12px;
        }

        .chart-head {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 8px;
        }

        .chart-title {
          font-size: 13px;
          font-weight: 650;
          line-height: 1.2;
        }

        .chart-values {
          color: var(--secondary-text-color);
          font-size: 11px;
          line-height: 1.35;
          text-align: right;
          white-space: nowrap;
          font-variant-numeric: tabular-nums;
        }

        .chart-svg,
        .chart-placeholder {
          display: block;
          width: 100%;
          height: 96px;
          border-radius: 8px;
          background: color-mix(in srgb, var(--primary-text-color) 4%, transparent);
        }

        .chart-placeholder {
          position: relative;
          overflow: hidden;
        }

        .chart-placeholder::after {
          content: "";
          position: absolute;
          inset: 0;
          background: linear-gradient(
            90deg,
            transparent,
            color-mix(in srgb, var(--primary-text-color) 8%, transparent),
            transparent
          );
          animation: shimmer 1.4s infinite;
        }

        .chart-line {
          fill: none;
          stroke-width: 2.2;
          vector-effect: non-scaling-stroke;
        }

        .chart-area {
          opacity: 0.16;
        }

        .chart-line.positive,
        .chart-area.positive {
          stroke: var(--success-color, #12805c);
          fill: var(--success-color, #12805c);
        }

        .chart-line.negative,
        .chart-area.negative {
          stroke: var(--error-color, #c62828);
          fill: var(--error-color, #c62828);
        }

        .chart-line.neutral,
        .chart-area.neutral {
          stroke: var(--primary-color);
          fill: var(--primary-color);
        }

        .table {
          overflow: visible;
        }

        .row {
          display: grid;
          grid-template-columns:
            minmax(72px, 1.2fr)
            minmax(58px, 0.9fr)
            minmax(58px, 0.9fr)
            minmax(58px, 0.9fr)
            minmax(58px, 0.9fr)
            minmax(48px, 0.75fr);
          gap: 8px;
          align-items: center;
          min-width: 0;
          padding: 10px 0;
          border-top: 1px solid var(--divider-color);
        }

        .head {
          color: var(--secondary-text-color);
          font-size: 12px;
          font-weight: 600;
          padding-top: 8px;
        }

        .coin,
        .num {
          min-width: 0;
        }

        .symbol {
          font-weight: 650;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .num {
          text-align: right;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: normal;
          overflow-wrap: anywhere;
          font-variant-numeric: tabular-nums;
          font-size: 13px;
          line-height: 1.22;
        }

        .positive {
          color: var(--success-color, #12805c);
        }

        .negative {
          color: var(--error-color, #c62828);
        }

        .neutral {
          color: var(--primary-text-color);
        }

        .empty {
          padding: 16px;
        }

        @keyframes shimmer {
          from {
            transform: translateX(-100%);
          }
          to {
            transform: translateX(100%);
          }
        }

        @media (max-width: 620px) {
          .card {
            padding: 12px;
          }

          .header {
            flex-direction: column;
          }

          .summary {
            text-align: left;
          }

          .metrics {
            grid-template-columns: 1fr;
          }

          .row {
            grid-template-columns:
              minmax(52px, 1fr)
              minmax(42px, 0.85fr)
              minmax(42px, 0.85fr)
              minmax(42px, 0.85fr)
              minmax(42px, 0.85fr)
              minmax(36px, 0.7fr);
            gap: 4px;
          }

          .head,
          .num {
            font-size: 10px;
          }

          .symbol {
            font-size: 11px;
          }

          .amount,
          .change {
            font-size: 10px;
          }

          .chart-svg,
          .chart-placeholder {
            height: 76px;
          }
        }
      </style>
    `;
  }
}

if (!customElements.get("crypto-portfolio-card")) {
  customElements.define("crypto-portfolio-card", CryptoPortfolioCard);
}

window.customCards = window.customCards || [];
const cryptoPortfolioCardInfo = {
  type: "crypto-portfolio-card",
  name: "Crypto Portfolio Card",
  description: "Shows a crypto portfolio overview from one sensor entity.",
  preview: true,
  documentationURL:
    "https://github.com/M-See/crypto_portfolio#dashboard-card",
  getEntitySuggestion: (hass, entityId) => {
    const state = hass.states[entityId];
    if (!state?.attributes?.positions) {
      return null;
    }
    return {
      config: {
        type: "custom:crypto-portfolio-card",
        entity: entityId,
      },
    };
  },
};
const existingCardInfo = window.customCards.find(
  (card) => card.type === cryptoPortfolioCardInfo.type
);
if (existingCardInfo) {
  Object.assign(existingCardInfo, cryptoPortfolioCardInfo);
} else {
  window.customCards.push(cryptoPortfolioCardInfo);
}
})();
