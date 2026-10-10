/* Full-page navigation is current policy; document$ also supports future rerenders. */
(() => {
  window.EuvicsNavigation?.dispose();
  let handlers;
  let subscription;
  const initialize = () => {
    handlers?.abort();
    handlers = new AbortController();
    const options = { signal: handlers.signal };
    const drawer = document.querySelector("#__drawer");
    const control = document.querySelector('.md-header label[for="__drawer"]');
    const navigation = document.querySelector(".md-nav--primary");
    if (!(drawer instanceof HTMLInputElement) || !(control instanceof HTMLElement)) return;
    if (navigation instanceof HTMLElement) {
      navigation.id = "primary-navigation";
      control.setAttribute("aria-controls", navigation.id);
    }
    control.setAttribute("role", "button");
    control.setAttribute("tabindex", "0");
    const updateState = () => {
      control.setAttribute("aria-expanded", String(drawer.checked));
      control.setAttribute("aria-label", drawer.checked ? "Close navigation" : "Open navigation");
    };
    control.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        event.stopPropagation();
        control.click();
      }
    }, options);
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && drawer.checked) {
        drawer.checked = false;
        drawer.dispatchEvent(new Event("change", { bubbles: true }));
        control.focus();
      }
    }, { ...options, capture: true });
    drawer.addEventListener("change", updateState, options);
    updateState();
  };
  const ready = () => {
    initialize();
    if (typeof document$ !== "undefined" && !subscription) {
      subscription = document$.subscribe(initialize);
    }
  };
  window.EuvicsNavigation = {
    initialize,
    dispose() {
      handlers?.abort();
      subscription?.unsubscribe();
      document.removeEventListener("DOMContentLoaded", ready);
      window.removeEventListener("pageshow", initialize);
    }
  };
  window.addEventListener("pageshow", initialize);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready, { once: true });
  else ready();
})();
