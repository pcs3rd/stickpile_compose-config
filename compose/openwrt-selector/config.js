/* exported config */
// OpenWrt Firmware Selector config (mounted over www/config.js by compose.yaml).
// Reference: https://github.com/openwrt/firmware-selector-openwrt-org#configuration

var config = {
  // Show help text for images
  show_help: true,

  // Versions and the default version are auto-detected from
  // <image_url>/.versions.json, so new OpenWrt releases show up by themselves.

  // Where stock images / .overview.json come from
  image_url: "https://downloads.openwrt.org",

  // Also list SNAPSHOT builds
  show_snapshots: true,

  // Info link URL
  info_url: "https://openwrt.org/start?do=search&id=toh&q={title} @toh",

  // Attended Sysupgrade server = our own ASU, routed by Traefik on the SAME origin
  // as this page (/api/v1 and /store), so Authentik's session cookie covers it.
  asu_url: "https://firmware.stickpile.net",

  // Packages added to every custom build (all OpenWrt devices here use apk)
  asu_extra_packages: ["luci", "luci-app-attendedsysupgrade"],
  // asu_extra_packages: ["luci", "luci-app-attendedsysupgrade", "tailscale", "openwisp-config"],
};
