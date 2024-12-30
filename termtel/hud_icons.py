def get_router_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 60 41">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="0.3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <g fill="none" stroke="#22D3EE" stroke-width="0.8" filter="url(#glow)">
    <!-- Base cylinder outlines -->
    <path d="M29.137 22.837c16.144 0 29.137-5.119 29.137-11.419S45.281 0 29.137 0 0 5.119 0 11.419s12.994 11.419 29.137 11.419z" opacity="0.4"/>
    <path d="M58.274 11.419c0 6.3-12.994 11.419-29.137 11.419S0 17.719 0 11.419v16.537c0 6.3 12.994 11.419 29.137 11.419s29.137-5.119 29.137-11.419z" opacity="0.4"/>

    <!-- Grid lines -->
    <path d="M14.5 11.419 h43.774" opacity="0.2"/>
    <path d="M29.137 5.419 v16.418" opacity="0.2"/>
    <path d="M43.774 11.419 h-43.774" opacity="0.2"/>

    <!-- Network connections -->
    <path d="M22.448 7.081l2.363 3.544-9.056 1.969 1.969-1.575L3.942 8.656 7.486 5.9l13.388 2.362 1.575-1.181z" stroke-width="1"/>
    <path d="M35.442 15.743L33.473 12.2l8.269-1.969-1.181 1.575 13.388 2.362-3.15 2.363-13.781-2.363-1.575 1.575z" stroke-width="1"/>
    <path d="M30.717 5.113l9.056-2.362.394 3.544-2.363-.394-4.331 3.938-4.331-.787 4.331-3.544-2.756-.394z" stroke-width="1"/>
    <path d="M26.78 19.288l-8.662 1.575-.394-4.331 2.756.787 4.725-4.331 4.331.787-5.119 4.725 2.362.788z" stroke-width="1"/>

    <!-- Corner brackets -->
    <path d="M2 2 h6 M2 2 v6" stroke-width="1"/>
    <path d="M58 2 h-6 M58 2 v6" stroke-width="1"/>
    <path d="M2 39 h6 M2 39 v-6" stroke-width="1"/>
    <path d="M58 39 h-6 M58 39 v-6" stroke-width="1"/>
  </g>
</svg>'''


def get_switch_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 41">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="0.3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <g fill="none" stroke="#22D3EE" stroke-width="0.8" filter="url(#glow)">
    <!-- Main switch body -->
    <path d="M15,10 h40 l-10,18 h-40 l10,-18z" opacity="0.4"/>
    <path d="M5,28 h40 v8 h-40z" opacity="0.4"/>
    <path d="M45,28 l10,-18 v8 l-10,18z" opacity="0.4"/>

    <!-- Network arrows -->
    <g stroke-width="1">
      <line x1="22" y1="15" x2="30" y2="15"/>
      <polygon points="23,18 17,15 23,12"/>

      <line x1="15" y1="23" x2="23" y2="23"/>
      <polygon points="16,26 10,23 16,20"/>

      <line x1="38" y1="22" x2="30" y2="22"/>
      <polygon points="37,19 43,22 37,25"/>

      <line x1="47" y1="14" x2="39" y2="14"/>
      <polygon points="46,11 52,14 46,17"/>
    </g>

    <!-- Corner brackets -->
    <path d="M2 2 h6 M2 2 v6" stroke-width="1"/>
    <path d="M58 2 h-6 M58 2 v6" stroke-width="1"/>
    <path d="M2 39 h6 M2 39 v-6" stroke-width="1"/>
    <path d="M58 39 h-6 M58 39 v-6" stroke-width="1"/>
  </g>
</svg>'''

def get_discovering_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 41">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="0.3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <g fill="none" stroke="#22D3EE" stroke-width="0.8" filter="url(#glow)">
    <!-- Base cylinder outlines -->
    <path d="M29.137 22.837c16.144 0 29.137-5.119 29.137-11.419S45.281 0 29.137 0 0 5.119 0 11.419s12.994 11.419 29.137 11.419z" opacity="0.4"/>
    <path d="M58.274 11.419c0 6.3-12.994 11.419-29.137 11.419S0 17.719 0 11.419v16.537c0 6.3 12.994 11.419 29.137 11.419s29.137-5.119 29.137-11.419z" opacity="0.4"/>

    <!-- Scanning line -->
    <line x1="0" y1="20" x2="60" y2="20" opacity="0.6">
      <animateTransform
        attributeName="transform"
        type="translate"
        from="0 -20"
        to="0 41"
        dur="2s"
        repeatCount="indefinite"/>
    </line>

    <!-- Pulsing circles -->
    <circle cx="30" cy="20" r="25" opacity="0.4">
      <animate
        attributeName="r"
        values="20;30"
        dur="1.5s"
        repeatCount="indefinite"/>
      <animate
        attributeName="opacity"
        values="0.4;0"
        dur="1.5s"
        repeatCount="indefinite"/>
    </circle>
    <circle cx="30" cy="20" r="25" opacity="0.4">
      <animate
        attributeName="r"
        values="20;30"
        dur="1.5s"
        begin="0.5s"
        repeatCount="indefinite"/>
      <animate
        attributeName="opacity"
        values="0.4;0"
        dur="1.5s"
        begin="0.5s"
        repeatCount="indefinite"/>
    </circle>

    <!-- Corner brackets -->
    <path d="M2 2 h6 M2 2 v6" stroke-width="1"/>
    <path d="M58 2 h-6 M58 2 v6" stroke-width="1"/>
    <path d="M2 39 h6 M2 39 v-6" stroke-width="1"/>
    <path d="M58 39 h-6 M58 39 v-6" stroke-width="1"/>
  </g>
</svg>'''


def get_unknown_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 41">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="0.3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <g fill="none" stroke="#22D3EE" stroke-width="0.8" filter="url(#glow)">
    <!-- Base outline - simplified generic network device -->
    <rect x="10" y="8" width="40" height="25" rx="2" opacity="0.4"/>

    <!-- Question mark -->
    <path d="M25 28h2v2h-2zM31 16c0-3-2.5-5-5.5-5S20 13 20 16h2c0-2 1.5-3 3.5-3s3.5 1 3.5 3c0 1-1 2-2.5 3-2 1.5-2.5 2.5-2.5 4h2c0-1 .5-2 2-3 2-1.5 3-2.5 3-4z" 
          opacity="0.8"/>

    <!-- Corner brackets -->
    <path d="M2 2 h6 M2 2 v6" stroke-width="1"/>
    <path d="M58 2 h-6 M58 2 v6" stroke-width="1"/>
    <path d="M2 39 h6 M2 39 v-6" stroke-width="1"/>
    <path d="M58 39 h-6 M58 39 v-6" stroke-width="1"/>
  </g>
</svg>'''