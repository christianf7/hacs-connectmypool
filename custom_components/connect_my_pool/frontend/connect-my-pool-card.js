const CARD_VERSION = "1.0.0";

const POOL_ICON = `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M2 20c1.5 0 2.5-1 2.5-1s1 1 2.5 1 2.5-1 2.5-1 1 1 2.5 1 2.5-1 2.5-1 1 1 2.5 1 2.5-1 2.5-1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M2 16c1.5 0 2.5-1 2.5-1s1 1 2.5 1 2.5-1 2.5-1 1 1 2.5 1 2.5-1 2.5-1 1 1 2.5 1 2.5-1 2.5-1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M6 12V4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  <path d="M18 12V4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  <path d="M6 8h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
</svg>`;

class ConnectMyPoolCard extends HTMLElement {
  _config = {};
  _hass = null;
  _entities = {};

  static getConfigElement() {
    return document.createElement("connect-my-pool-card-editor");
  }

  static getStubConfig() {
    return { title: "My Pool" };
  }

  set hass(hass) {
    this._hass = hass;
    this._discoverEntities();
    this._render();
  }

  setConfig(config) {
    this._config = {
      title: "My Pool",
      show_header: true,
      compact: false,
      ...config,
    };
  }

  getCardSize() {
    return 6;
  }

  _discoverEntities() {
    if (!this._hass) return;

    const all = Object.keys(this._hass.states);
    const cmp = all.filter((e) => {
      const s = this._hass.states[e];
      return (
        s &&
        s.attributes &&
        s.attributes.device_class !== undefined &&
        e.includes("connect_my_pool")
      ) || e.includes("connect_my_pool");
    });

    this._entities = {
      temperature: cmp.find(
        (e) =>
          e.startsWith("sensor.") &&
          this._hass.states[e]?.attributes?.device_class === "temperature"
      ),
      heaters: cmp.filter(
        (e) => e.startsWith("climate.")
      ),
      lights: cmp.filter(
        (e) => e.startsWith("light.")
      ),
      switches: cmp.filter(
        (e) => e.startsWith("switch.")
      ),
      selects: cmp.filter(
        (e) => e.startsWith("select.")
      ),
      numbers: cmp.filter(
        (e) => e.startsWith("number.")
      ),
      buttons: cmp.filter(
        (e) => e.startsWith("button.")
      ),
    };
  }

  _getState(entityId) {
    if (!entityId || !this._hass) return null;
    return this._hass.states[entityId] || null;
  }

  _callService(domain, service, data) {
    if (!this._hass) return;
    this._hass.callService(domain, service, data);
  }

  _render() {
    if (!this._hass) return;

    const tempState = this._getState(this._entities.temperature);
    const tempVal = tempState ? parseFloat(tempState.state) : null;
    const tempUnit = tempState?.attributes?.unit_of_measurement || "°C";

    const poolSpaSelect = this._entities.selects.find((e) => {
      const s = this._getState(e);
      return s && (s.attributes?.friendly_name || "").toLowerCase().includes("pool / spa");
    });
    const poolSpaState = this._getState(poolSpaSelect);

    const favouriteSelect = this._entities.selects.find((e) => {
      const s = this._getState(e);
      return s && (s.attributes?.friendly_name || "").toLowerCase().includes("favourite");
    });

    const channelSelects = this._entities.selects.filter((e) => {
      const s = this._getState(e);
      const name = (s?.attributes?.friendly_name || "").toLowerCase();
      return s && !name.includes("pool / spa") && !name.includes("favourite") &&
             !name.includes("solar") && !name.includes("valve");
    });

    const solarSelects = this._entities.selects.filter((e) => {
      const s = this._getState(e);
      return s && (s.attributes?.friendly_name || "").toLowerCase().includes("solar");
    });

    const valveSelects = this._entities.selects.filter((e) => {
      const s = this._getState(e);
      return s && (s.attributes?.friendly_name || "").toLowerCase().includes("valve");
    });

    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <ha-card>
        ${this._config.show_header !== false ? this._renderHeader(tempVal, tempUnit, poolSpaState) : ""}
        <div class="card-body">
          ${this._renderTemperatureRing(tempVal, tempUnit)}
          ${this._renderHeaters()}
          ${this._renderEquipmentGrid(channelSelects)}
          ${this._renderSwitches()}
          ${this._renderLights()}
          ${this._renderSolar(solarSelects)}
          ${this._renderValves(valveSelects)}
          ${favouriteSelect ? this._renderFavourites(favouriteSelect) : ""}
        </div>
      </ha-card>
    `;

    this._attachEventListeners();
  }

  _styles() {
    return `
      :host {
        --cmp-primary: #0ea5e9;
        --cmp-primary-dark: #0284c7;
        --cmp-primary-light: #38bdf8;
        --cmp-accent: #06b6d4;
        --cmp-warm: #f59e0b;
        --cmp-warm-glow: #fbbf24;
        --cmp-cool: #6366f1;
        --cmp-success: #10b981;
        --cmp-danger: #ef4444;
        --cmp-surface: var(--card-background-color, #1e293b);
        --cmp-surface-elevated: var(--primary-background-color, #0f172a);
        --cmp-text: var(--primary-text-color, #f1f5f9);
        --cmp-text-secondary: var(--secondary-text-color, #94a3b8);
        --cmp-border: rgba(148, 163, 184, 0.1);
        --cmp-radius: 16px;
        --cmp-radius-sm: 10px;
        --cmp-transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      }

      ha-card {
        background: var(--cmp-surface);
        border: none;
        overflow: hidden;
        font-family: var(--ha-card-header-font-family, inherit);
      }

      .card-header {
        position: relative;
        padding: 24px 24px 16px;
        background: linear-gradient(135deg,
          rgba(14, 165, 233, 0.12) 0%,
          rgba(6, 182, 212, 0.06) 50%,
          transparent 100%
        );
        border-bottom: 1px solid var(--cmp-border);
        overflow: hidden;
      }

      .card-header::before {
        content: '';
        position: absolute;
        top: -60%;
        right: -20%;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(14, 165, 233, 0.08) 0%, transparent 70%);
        pointer-events: none;
      }

      .header-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: relative;
        z-index: 1;
      }

      .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .header-icon {
        width: 36px;
        height: 36px;
        color: var(--cmp-primary);
        filter: drop-shadow(0 0 8px rgba(14, 165, 233, 0.3));
        flex-shrink: 0;
      }

      .header-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--cmp-text);
        letter-spacing: -0.01em;
      }

      .header-subtitle {
        font-size: 12px;
        color: var(--cmp-text-secondary);
        margin-top: 2px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .header-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.02em;
        transition: var(--cmp-transition);
      }

      .badge-pool {
        background: rgba(14, 165, 233, 0.15);
        color: var(--cmp-primary-light);
        border: 1px solid rgba(14, 165, 233, 0.2);
      }

      .badge-spa {
        background: rgba(245, 158, 11, 0.15);
        color: var(--cmp-warm-glow);
        border: 1px solid rgba(245, 158, 11, 0.2);
      }

      .badge-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        animation: pulse-dot 2s ease-in-out infinite;
      }

      .badge-pool .badge-dot { background: var(--cmp-primary-light); }
      .badge-spa .badge-dot { background: var(--cmp-warm-glow); }

      @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
      }

      .card-body {
        padding: 20px 24px 24px;
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      /* Temperature ring */
      .temp-ring-container {
        display: flex;
        justify-content: center;
        padding: 8px 0;
      }

      .temp-ring {
        position: relative;
        width: 140px;
        height: 140px;
      }

      .temp-ring svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
      }

      .temp-ring-bg {
        fill: none;
        stroke: var(--cmp-border);
        stroke-width: 6;
      }

      .temp-ring-fill {
        fill: none;
        stroke-width: 6;
        stroke-linecap: round;
        transition: stroke-dashoffset 1s ease, stroke 0.5s ease;
      }

      .temp-ring-center {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
      }

      .temp-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--cmp-text);
        line-height: 1;
        letter-spacing: -0.02em;
      }

      .temp-unit {
        font-size: 14px;
        font-weight: 400;
        color: var(--cmp-text-secondary);
      }

      .temp-label {
        font-size: 11px;
        color: var(--cmp-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 4px;
      }

      /* Section */
      .section {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .section-title {
        font-size: 11px;
        font-weight: 600;
        color: var(--cmp-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding-left: 2px;
      }

      /* Equipment grid */
      .equipment-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 10px;
      }

      .equip-tile {
        position: relative;
        background: var(--cmp-surface-elevated);
        border: 1px solid var(--cmp-border);
        border-radius: var(--cmp-radius-sm);
        padding: 14px;
        cursor: pointer;
        transition: var(--cmp-transition);
        overflow: hidden;
        -webkit-tap-highlight-color: transparent;
        user-select: none;
      }

      .equip-tile:active {
        transform: scale(0.97);
      }

      .equip-tile::before {
        content: '';
        position: absolute;
        inset: 0;
        opacity: 0;
        transition: opacity var(--cmp-transition);
        pointer-events: none;
        border-radius: inherit;
      }

      .equip-tile.on::before {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.08), transparent);
        opacity: 1;
      }

      .equip-tile.on {
        border-color: rgba(14, 165, 233, 0.3);
      }

      .equip-tile-icon {
        width: 28px;
        height: 28px;
        margin-bottom: 10px;
        color: var(--cmp-text-secondary);
        transition: var(--cmp-transition);
      }

      .equip-tile.on .equip-tile-icon {
        color: var(--cmp-primary-light);
        filter: drop-shadow(0 0 6px rgba(14, 165, 233, 0.4));
      }

      .equip-tile-name {
        font-size: 12px;
        font-weight: 500;
        color: var(--cmp-text);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 4px;
      }

      .equip-tile-state {
        font-size: 11px;
        color: var(--cmp-text-secondary);
        font-weight: 500;
      }

      .equip-tile.on .equip-tile-state {
        color: var(--cmp-primary-light);
      }

      /* Climate tile */
      .climate-tile {
        background: var(--cmp-surface-elevated);
        border: 1px solid var(--cmp-border);
        border-radius: var(--cmp-radius);
        padding: 18px;
        transition: var(--cmp-transition);
      }

      .climate-tile.heating {
        border-color: rgba(245, 158, 11, 0.3);
        background: linear-gradient(135deg,
          rgba(245, 158, 11, 0.06),
          var(--cmp-surface-elevated)
        );
      }

      .climate-tile.cooling {
        border-color: rgba(99, 102, 241, 0.3);
        background: linear-gradient(135deg,
          rgba(99, 102, 241, 0.06),
          var(--cmp-surface-elevated)
        );
      }

      .climate-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
      }

      .climate-info {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .climate-icon {
        width: 24px;
        height: 24px;
      }

      .climate-icon.heat { color: var(--cmp-warm); }
      .climate-icon.cool { color: var(--cmp-cool); }
      .climate-icon.off { color: var(--cmp-text-secondary); }

      .climate-name {
        font-size: 14px;
        font-weight: 600;
        color: var(--cmp-text);
      }

      .climate-mode-badge {
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }

      .climate-mode-badge.heat {
        background: rgba(245, 158, 11, 0.15);
        color: var(--cmp-warm-glow);
      }

      .climate-mode-badge.cool {
        background: rgba(99, 102, 241, 0.15);
        color: #818cf8;
      }

      .climate-mode-badge.off {
        background: rgba(148, 163, 184, 0.1);
        color: var(--cmp-text-secondary);
      }

      .climate-temps {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
      }

      .climate-temp-block {
        text-align: center;
      }

      .climate-temp-label {
        font-size: 10px;
        color: var(--cmp-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
      }

      .climate-temp-value {
        font-size: 22px;
        font-weight: 700;
        color: var(--cmp-text);
      }

      .climate-target-controls {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .climate-temp-btn {
        width: 32px;
        height: 32px;
        border: 1px solid var(--cmp-border);
        border-radius: 50%;
        background: var(--cmp-surface);
        color: var(--cmp-text);
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: var(--cmp-transition);
        -webkit-tap-highlight-color: transparent;
      }

      .climate-temp-btn:hover {
        background: rgba(14, 165, 233, 0.1);
        border-color: rgba(14, 165, 233, 0.3);
      }

      .climate-temp-btn:active {
        transform: scale(0.9);
      }

      /* Light tile */
      .light-tile {
        background: var(--cmp-surface-elevated);
        border: 1px solid var(--cmp-border);
        border-radius: var(--cmp-radius-sm);
        padding: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: pointer;
        transition: var(--cmp-transition);
        -webkit-tap-highlight-color: transparent;
      }

      .light-tile.on {
        border-color: rgba(251, 191, 36, 0.3);
        background: linear-gradient(135deg,
          rgba(251, 191, 36, 0.06),
          var(--cmp-surface-elevated)
        );
      }

      .light-tile:active {
        transform: scale(0.98);
      }

      .light-left {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .light-icon {
        width: 28px;
        height: 28px;
        color: var(--cmp-text-secondary);
        transition: var(--cmp-transition);
      }

      .light-tile.on .light-icon {
        color: var(--cmp-warm-glow);
        filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.5));
      }

      .light-info {
        display: flex;
        flex-direction: column;
      }

      .light-name {
        font-size: 13px;
        font-weight: 500;
        color: var(--cmp-text);
      }

      .light-effect {
        font-size: 11px;
        color: var(--cmp-text-secondary);
        margin-top: 2px;
      }

      /* Toggle switch */
      .toggle-track {
        position: relative;
        width: 44px;
        height: 24px;
        border-radius: 12px;
        background: rgba(148, 163, 184, 0.2);
        transition: var(--cmp-transition);
        cursor: pointer;
        flex-shrink: 0;
      }

      .toggle-track.on {
        background: var(--cmp-primary);
      }

      .toggle-thumb {
        position: absolute;
        top: 2px;
        left: 2px;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: white;
        transition: var(--cmp-transition);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
      }

      .toggle-track.on .toggle-thumb {
        left: 22px;
      }

      /* Select dropdown */
      .select-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--cmp-surface-elevated);
        border: 1px solid var(--cmp-border);
        border-radius: var(--cmp-radius-sm);
        padding: 12px 14px;
      }

      .select-left {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .select-icon {
        width: 22px;
        height: 22px;
        color: var(--cmp-text-secondary);
      }

      .select-name {
        font-size: 13px;
        font-weight: 500;
        color: var(--cmp-text);
      }

      .select-dropdown {
        appearance: none;
        -webkit-appearance: none;
        background: var(--cmp-surface);
        border: 1px solid var(--cmp-border);
        border-radius: 8px;
        padding: 6px 28px 6px 10px;
        font-size: 12px;
        font-weight: 500;
        color: var(--cmp-text);
        cursor: pointer;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 8px center;
        transition: var(--cmp-transition);
        max-width: 140px;
      }

      .select-dropdown:focus {
        outline: none;
        border-color: var(--cmp-primary);
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.15);
      }

      /* Solar tile */
      .solar-tile {
        background: var(--cmp-surface-elevated);
        border: 1px solid var(--cmp-border);
        border-radius: var(--cmp-radius-sm);
        padding: 14px;
      }

      .solar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
      }

      .solar-left {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .solar-icon {
        width: 24px;
        height: 24px;
        color: var(--cmp-warm);
      }

      .solar-name {
        font-size: 13px;
        font-weight: 500;
        color: var(--cmp-text);
      }

      /* Favourite tile */
      .fav-container {
        background: var(--cmp-surface-elevated);
        border: 1px solid var(--cmp-border);
        border-radius: var(--cmp-radius-sm);
        padding: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .fav-left {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .fav-icon {
        width: 22px;
        height: 22px;
        color: var(--cmp-accent);
      }

      .fav-name {
        font-size: 13px;
        font-weight: 500;
        color: var(--cmp-text);
      }

      /* Button */
      .sync-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border: 1px solid var(--cmp-border);
        border-radius: 8px;
        background: var(--cmp-surface);
        color: var(--cmp-text-secondary);
        font-size: 11px;
        font-weight: 500;
        cursor: pointer;
        transition: var(--cmp-transition);
        -webkit-tap-highlight-color: transparent;
      }

      .sync-btn:hover {
        background: rgba(14, 165, 233, 0.1);
        border-color: rgba(14, 165, 233, 0.3);
        color: var(--cmp-primary-light);
      }

      .sync-btn:active {
        transform: scale(0.95);
      }

      .sync-btn svg {
        width: 14px;
        height: 14px;
      }

      .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: var(--cmp-text-secondary);
      }

      .empty-state-icon {
        width: 48px;
        height: 48px;
        margin: 0 auto 12px;
        color: var(--cmp-primary);
        opacity: 0.5;
      }

      .empty-state-text {
        font-size: 14px;
        font-weight: 500;
      }

      .empty-state-sub {
        font-size: 12px;
        margin-top: 4px;
        opacity: 0.7;
      }

      @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
      }
    `;
  }

  _renderHeader(tempVal, tempUnit, poolSpaState) {
    const title = this._config.title || "My Pool";
    const mode = poolSpaState?.state || "Pool";
    const isPool = mode.toLowerCase() === "pool";

    return `
      <div class="card-header">
        <div class="header-top">
          <div class="header-left">
            <div class="header-icon">${POOL_ICON}</div>
            <div>
              <div class="header-title">${title}</div>
              <div class="header-subtitle">
                ${tempVal !== null ? `${tempVal}${tempUnit} Water` : "AstralPool System"}
              </div>
            </div>
          </div>
          ${poolSpaState ? `
            <div class="header-badge ${isPool ? "badge-pool" : "badge-spa"}">
              <span class="badge-dot"></span>
              ${mode}
            </div>
          ` : ""}
        </div>
      </div>
    `;
  }

  _renderTemperatureRing(tempVal, tempUnit) {
    if (tempVal === null) return "";

    const minTemp = 5;
    const maxTemp = 45;
    const pct = Math.min(1, Math.max(0, (tempVal - minTemp) / (maxTemp - minTemp)));
    const circumference = 2 * Math.PI * 56;
    const offset = circumference * (1 - pct * 0.75);

    let color;
    if (tempVal < 20) color = "#6366f1";
    else if (tempVal < 26) color = "#0ea5e9";
    else if (tempVal < 32) color = "#10b981";
    else if (tempVal < 36) color = "#f59e0b";
    else color = "#ef4444";

    return `
      <div class="temp-ring-container">
        <div class="temp-ring">
          <svg viewBox="0 0 120 120">
            <circle class="temp-ring-bg" cx="60" cy="60" r="56"
              stroke-dasharray="${circumference}"
              stroke-dashoffset="${circumference * 0.25}" />
            <circle class="temp-ring-fill" cx="60" cy="60" r="56"
              stroke="${color}"
              stroke-dasharray="${circumference}"
              stroke-dashoffset="${offset}" />
          </svg>
          <div class="temp-ring-center">
            <div class="temp-value">${tempVal}<span class="temp-unit">${tempUnit}</span></div>
            <div class="temp-label">Water</div>
          </div>
        </div>
      </div>
    `;
  }

  _renderHeaters() {
    if (!this._entities.heaters.length) return "";

    return this._entities.heaters.map((entityId) => {
      const state = this._getState(entityId);
      if (!state) return "";

      const mode = state.state;
      const current = state.attributes.current_temperature;
      const target = state.attributes.temperature;
      const name = state.attributes.friendly_name?.replace("Connect My Pool ", "") || "Heater";

      const isHeat = mode === "heat";
      const isCool = mode === "cool";
      const isOff = mode === "off";

      const modeClass = isHeat ? "heating" : isCool ? "cooling" : "";
      const iconClass = isHeat ? "heat" : isCool ? "cool" : "off";
      const modeLabel = isHeat ? "Heating" : isCool ? "Cooling" : "Off";
      const badgeClass = isHeat ? "heat" : isCool ? "cool" : "off";

      const iconSvg = isHeat
        ? `<svg viewBox="0 0 24 24" fill="none"><path d="M12 2v8l3 3M12 22a7 7 0 100-14 7 7 0 000 14z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
        : isCool
        ? `<svg viewBox="0 0 24 24" fill="none"><path d="M12 2v20M17 7l-5 5-5-5M7 17l5-5 5 5M2 12h20M7 7l-5 5 5 5M17 7l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
        : `<svg viewBox="0 0 24 24" fill="none"><path d="M12 9a3 3 0 100 6 3 3 0 000-6zM12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`;

      return `
        <div class="section">
          <div class="section-title">Heater</div>
          <div class="climate-tile ${modeClass}" data-entity="${entityId}">
            <div class="climate-header">
              <div class="climate-info">
                <div class="climate-icon ${iconClass}">${iconSvg}</div>
                <div class="climate-name">${name}</div>
              </div>
              <span class="climate-mode-badge ${badgeClass}">${modeLabel}</span>
            </div>
            <div class="climate-temps">
              <div class="climate-temp-block">
                <div class="climate-temp-label">Current</div>
                <div class="climate-temp-value">${current != null ? `${current}°` : "—"}</div>
              </div>
              ${!isOff && target != null ? `
                <div class="climate-temp-block">
                  <div class="climate-temp-label">Target</div>
                  <div class="climate-target-controls">
                    <button class="climate-temp-btn" data-action="temp-down" data-entity="${entityId}">−</button>
                    <div class="climate-temp-value">${target}°</div>
                    <button class="climate-temp-btn" data-action="temp-up" data-entity="${entityId}">+</button>
                  </div>
                </div>
              ` : ""}
            </div>
          </div>
        </div>
      `;
    }).join("");
  }

  _renderEquipmentGrid(channelSelects) {
    if (!channelSelects.length) return "";

    const tiles = channelSelects.map((entityId) => {
      const state = this._getState(entityId);
      if (!state) return "";

      const name = state.attributes.friendly_name?.replace("Connect My Pool ", "") || "Channel";
      const current = state.state;
      const isOn = current.toLowerCase() !== "off";
      const options = state.attributes.options || [];

      const iconSvg = this._getEquipmentIcon(name);

      return `
        <div class="equip-tile ${isOn ? "on" : ""}" data-entity="${entityId}" data-type="select-cycle">
          <div class="equip-tile-icon">${iconSvg}</div>
          <div class="equip-tile-name">${name}</div>
          <div class="equip-tile-state">${current}</div>
        </div>
      `;
    }).join("");

    return `
      <div class="section">
        <div class="section-title">Equipment</div>
        <div class="equipment-grid">${tiles}</div>
      </div>
    `;
  }

  _renderSwitches() {
    if (!this._entities.switches.length) return "";

    const tiles = this._entities.switches.map((entityId) => {
      const state = this._getState(entityId);
      if (!state) return "";

      const name = state.attributes.friendly_name?.replace("Connect My Pool ", "") || "Switch";
      const isOn = state.state === "on";
      const iconSvg = this._getEquipmentIcon(name);

      return `
        <div class="equip-tile ${isOn ? "on" : ""}" data-entity="${entityId}" data-type="switch-toggle">
          <div class="equip-tile-icon">${iconSvg}</div>
          <div class="equip-tile-name">${name}</div>
          <div class="equip-tile-state">${isOn ? "On" : "Off"}</div>
        </div>
      `;
    }).join("");

    return `
      <div class="section">
        <div class="section-title">Switches</div>
        <div class="equipment-grid">${tiles}</div>
      </div>
    `;
  }

  _renderLights() {
    if (!this._entities.lights.length) return "";

    const syncButtons = this._entities.buttons;

    const items = this._entities.lights.map((entityId) => {
      const state = this._getState(entityId);
      if (!state) return "";

      const name = state.attributes.friendly_name?.replace("Connect My Pool ", "") || "Light";
      const isOn = state.state === "on";
      const effect = state.attributes.effect || null;

      const matchingSync = syncButtons.find((b) => {
        const bs = this._getState(b);
        return bs && (bs.attributes.friendly_name || "").toLowerCase().includes(name.toLowerCase());
      });

      return `
        <div class="light-tile ${isOn ? "on" : ""}" data-entity="${entityId}" data-type="light-toggle">
          <div class="light-left">
            <div class="light-icon">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M9 21h6M12 3a6 6 0 014 10.5V17H8v-3.5A6 6 0 0112 3z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="light-info">
              <div class="light-name">${name}</div>
              ${effect ? `<div class="light-effect">${effect}</div>` : ""}
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            ${matchingSync ? `
              <button class="sync-btn" data-entity="${matchingSync}" data-type="button-press" title="Sync colour">
                <svg viewBox="0 0 24 24" fill="none"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10M23 14l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            ` : ""}
            <div class="toggle-track ${isOn ? "on" : ""}" data-entity="${entityId}" data-type="light-toggle-switch">
              <div class="toggle-thumb"></div>
            </div>
          </div>
        </div>
      `;
    }).join("");

    return `
      <div class="section">
        <div class="section-title">Lighting</div>
        ${items}
      </div>
    `;
  }

  _renderSolar(solarSelects) {
    if (!solarSelects.length && !this._entities.numbers.length) return "";

    const items = solarSelects.map((entityId) => {
      const state = this._getState(entityId);
      if (!state) return "";

      const name = state.attributes.friendly_name?.replace("Connect My Pool ", "") || "Solar";
      const current = state.state;
      const options = state.attributes.options || [];

      const matchingNum = this._entities.numbers.find((n) => {
        const ns = this._getState(n);
        return ns && (ns.attributes.friendly_name || "").toLowerCase().includes("solar");
      });
      const numState = this._getState(matchingNum);

      return `
        <div class="solar-tile">
          <div class="solar-header">
            <div class="solar-left">
              <div class="solar-icon">
                <svg viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="solar-name">${name}</div>
            </div>
            <select class="select-dropdown" data-entity="${entityId}" data-type="select-option">
              ${options.map((o) => `<option value="${o}" ${o === current ? "selected" : ""}>${o}</option>`).join("")}
            </select>
          </div>
          ${numState ? `
            <div class="climate-temps" style="padding-top: 6px;">
              <div class="climate-temp-block">
                <div class="climate-temp-label">Target Temperature</div>
                <div class="climate-target-controls">
                  <button class="climate-temp-btn" data-action="num-down" data-entity="${matchingNum}">−</button>
                  <div class="climate-temp-value">${numState.state}°</div>
                  <button class="climate-temp-btn" data-action="num-up" data-entity="${matchingNum}">+</button>
                </div>
              </div>
            </div>
          ` : ""}
        </div>
      `;
    }).join("");

    return `
      <div class="section">
        <div class="section-title">Solar</div>
        ${items}
      </div>
    `;
  }

  _renderValves(valveSelects) {
    if (!valveSelects.length) return "";

    const items = valveSelects.map((entityId) => {
      const state = this._getState(entityId);
      if (!state) return "";

      const name = state.attributes.friendly_name?.replace("Connect My Pool ", "") || "Valve";
      const current = state.state;
      const options = state.attributes.options || [];

      return `
        <div class="select-row">
          <div class="select-left">
            <div class="select-icon">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 2v6M12 16v6M2 12h6M16 12h6M7 7l3 3M14 14l3 3M17 7l-3 3M10 14l-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="select-name">${name}</div>
          </div>
          <select class="select-dropdown" data-entity="${entityId}" data-type="select-option">
            ${options.map((o) => `<option value="${o}" ${o === current ? "selected" : ""}>${o}</option>`).join("")}
          </select>
        </div>
      `;
    }).join("");

    return `
      <div class="section">
        <div class="section-title">Valves</div>
        ${items}
      </div>
    `;
  }

  _renderFavourites(entityId) {
    const state = this._getState(entityId);
    if (!state) return "";

    const current = state.state;
    const options = state.attributes.options || [];

    return `
      <div class="section">
        <div class="section-title">Favourites</div>
        <div class="fav-container">
          <div class="fav-left">
            <div class="fav-icon">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.27 5.82 22 7 14.14l-5-4.87 6.91-1.01L12 2z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="fav-name">Favourite</div>
          </div>
          <select class="select-dropdown" data-entity="${entityId}" data-type="select-option">
            <option value="" ${!current || current === "unknown" ? "selected" : ""}>None</option>
            ${options.map((o) => `<option value="${o}" ${o === current ? "selected" : ""}>${o}</option>`).join("")}
          </select>
        </div>
      </div>
    `;
  }

  _getEquipmentIcon(name) {
    const n = name.toLowerCase();

    if (n.includes("filter") || n.includes("pump"))
      return `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/><path d="M12 8v4l2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

    if (n.includes("blower"))
      return `<svg viewBox="0 0 24 24" fill="none"><path d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1011 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

    if (n.includes("jet") || n.includes("spa"))
      return `<svg viewBox="0 0 24 24" fill="none"><path d="M2 12c2-3 4-3 6 0s4 3 6 0 4-3 6 0M2 6c2-3 4-3 6 0s4 3 6 0 4-3 6 0M2 18c2-3 4-3 6 0s4 3 6 0 4-3 6 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`;

    if (n.includes("waterfall") || n.includes("fountain") || n.includes("overflow") || n.includes("spillway"))
      return `<svg viewBox="0 0 24 24" fill="none"><path d="M12 2v6M8 4v8M16 4v8M4 8v6M20 8v6M7 16c0 2.5 2.5 4 5 4s5-1.5 5-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`;

    if (n.includes("audio") || n.includes("music"))
      return `<svg viewBox="0 0 24 24" fill="none"><path d="M9 18V5l12-2v13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="1.5"/><circle cx="18" cy="16" r="3" stroke="currentColor" stroke-width="1.5"/></svg>`;

    if (n.includes("swim"))
      return `<svg viewBox="0 0 24 24" fill="none"><circle cx="19" cy="4" r="2" stroke="currentColor" stroke-width="1.5"/><path d="M13 7l-2 4h4l-2 4M2 18c1.5 0 2.5-1 2.5-1s1 1 2.5 1 2.5-1 2.5-1 1 1 2.5 1 2.5-1 2.5-1 1 1 2.5 1 2.5-1 2.5-1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

    if (n.includes("heater") || n.includes("heat"))
      return `<svg viewBox="0 0 24 24" fill="none"><path d="M12 2v8l3 3M12 22a7 7 0 100-14 7 7 0 000 14z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

    return `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`;
  }

  _attachEventListeners() {
    if (!this.shadowRoot) return;

    this.shadowRoot.querySelectorAll('[data-type="select-cycle"]').forEach((el) => {
      el.addEventListener("click", () => {
        const entityId = el.dataset.entity;
        const state = this._getState(entityId);
        if (!state) return;

        const options = state.attributes.options || [];
        const current = state.state;
        const idx = options.indexOf(current);
        const next = options[(idx + 1) % options.length];

        this._callService("select", "select_option", {
          entity_id: entityId,
          option: next,
        });
      });
    });

    this.shadowRoot.querySelectorAll('[data-type="switch-toggle"]').forEach((el) => {
      el.addEventListener("click", () => {
        const entityId = el.dataset.entity;
        const state = this._getState(entityId);
        if (!state) return;

        const service = state.state === "on" ? "turn_off" : "turn_on";
        this._callService("switch", service, { entity_id: entityId });
      });
    });

    this.shadowRoot.querySelectorAll('[data-type="light-toggle"], [data-type="light-toggle-switch"]').forEach((el) => {
      el.addEventListener("click", (e) => {
        if (e.target.closest(".sync-btn") || e.target.closest('[data-type="light-toggle-switch"]') !== el && el.dataset.type === "light-toggle") {
          if (el.dataset.type === "light-toggle" && !e.target.closest('[data-type="light-toggle-switch"]') && !e.target.closest(".sync-btn")) {
            const entityId = el.dataset.entity;
            this._fireEvent("hass-more-info", { entityId });
          }
          return;
        }
        const entityId = el.dataset.entity || el.closest("[data-entity]")?.dataset.entity;
        if (!entityId) return;
        const state = this._getState(entityId);
        if (!state) return;
        const service = state.state === "on" ? "turn_off" : "turn_on";
        this._callService("light", service, { entity_id: entityId });
        e.stopPropagation();
      });
    });

    this.shadowRoot.querySelectorAll('[data-type="button-press"]').forEach((el) => {
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        const entityId = el.dataset.entity;
        this._callService("button", "press", { entity_id: entityId });
      });
    });

    this.shadowRoot.querySelectorAll('[data-type="select-option"]').forEach((el) => {
      el.addEventListener("change", (e) => {
        e.stopPropagation();
        const entityId = el.dataset.entity;
        const value = el.value;
        if (!value) return;
        this._callService("select", "select_option", {
          entity_id: entityId,
          option: value,
        });
      });
    });

    this.shadowRoot.querySelectorAll('[data-action="temp-down"], [data-action="temp-up"]').forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const entityId = btn.dataset.entity;
        const state = this._getState(entityId);
        if (!state) return;

        const current = state.attributes.temperature;
        if (current == null) return;

        const delta = btn.dataset.action === "temp-up" ? 1 : -1;
        const next = Math.min(40, Math.max(10, current + delta));

        this._callService("climate", "set_temperature", {
          entity_id: entityId,
          temperature: next,
        });
      });
    });

    this.shadowRoot.querySelectorAll('[data-action="num-down"], [data-action="num-up"]').forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const entityId = btn.dataset.entity;
        const state = this._getState(entityId);
        if (!state) return;

        const current = parseFloat(state.state);
        if (isNaN(current)) return;

        const step = state.attributes.step || 1;
        const min = state.attributes.min || 10;
        const max = state.attributes.max || 40;
        const delta = btn.dataset.action === "num-up" ? step : -step;
        const next = Math.min(max, Math.max(min, current + delta));

        this._callService("number", "set_value", {
          entity_id: entityId,
          value: next,
        });
      });
    });

    this.shadowRoot.querySelectorAll(".climate-tile").forEach((el) => {
      el.addEventListener("click", (e) => {
        if (e.target.closest(".climate-temp-btn")) return;
        const entityId = el.dataset.entity;
        this._fireEvent("hass-more-info", { entityId });
      });
    });

    const badge = this.shadowRoot.querySelector(".header-badge");
    if (badge) {
      const poolSpaSelect = this._entities.selects.find((eid) => {
        const s = this._getState(eid);
        return s && (s.attributes?.friendly_name || "").toLowerCase().includes("pool / spa");
      });
      if (poolSpaSelect) {
        badge.style.cursor = "pointer";
        badge.addEventListener("click", () => {
          const state = this._getState(poolSpaSelect);
          if (!state) return;
          const next = state.state === "Pool" ? "Spa" : "Pool";
          this._callService("select", "select_option", {
            entity_id: poolSpaSelect,
            option: next,
          });
        });
      }
    }
  }

  _fireEvent(type, detail) {
    const event = new CustomEvent(type, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }
}

class ConnectMyPoolCardEditor extends HTMLElement {
  _config = {};
  _hass = null;

  set hass(hass) {
    this._hass = hass;
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }

    this.shadowRoot.innerHTML = `
      <style>
        .editor {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .field {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        label {
          font-size: 12px;
          font-weight: 500;
          color: var(--secondary-text-color);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        input, select {
          padding: 8px 12px;
          border: 1px solid var(--divider-color, #444);
          border-radius: 8px;
          background: var(--primary-background-color);
          color: var(--primary-text-color);
          font-size: 14px;
        }
        input:focus, select:focus {
          outline: none;
          border-color: var(--primary-color);
        }
        .checkbox-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .checkbox-row input[type="checkbox"] {
          width: 18px;
          height: 18px;
        }
        .checkbox-row label {
          text-transform: none;
          font-size: 14px;
          color: var(--primary-text-color);
        }
      </style>
      <div class="editor">
        <div class="field">
          <label>Card Title</label>
          <input type="text" id="title" value="${this._config.title || "My Pool"}" />
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="show_header" ${this._config.show_header !== false ? "checked" : ""} />
          <label for="show_header">Show header</label>
        </div>
      </div>
    `;

    this.shadowRoot.getElementById("title").addEventListener("input", (e) => {
      this._config = { ...this._config, title: e.target.value };
      this._dispatch();
    });

    this.shadowRoot.getElementById("show_header").addEventListener("change", (e) => {
      this._config = { ...this._config, show_header: e.target.checked };
      this._dispatch();
    });
  }

  _dispatch() {
    const event = new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

customElements.define("connect-my-pool-card", ConnectMyPoolCard);
customElements.define("connect-my-pool-card-editor", ConnectMyPoolCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "connect-my-pool-card",
  name: "Connect My Pool",
  description: "A beautiful pool control card for AstralPool systems via ConnectMyPool.",
  preview: true,
  documentationURL: "https://github.com/christianf7/hacs-connectmypool",
});

console.info(
  `%c CONNECT MY POOL CARD %c v${CARD_VERSION} `,
  "color: #fff; background: #0ea5e9; font-weight: bold; padding: 2px 6px; border-radius: 4px 0 0 4px;",
  "color: #0ea5e9; background: #0f172a; font-weight: bold; padding: 2px 6px; border-radius: 0 4px 4px 0;"
);
