document.addEventListener("DOMContentLoaded", () => {
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
  control.setAttribute("aria-label", "Open navigation");

  const updateState = () => {
    control.setAttribute("aria-expanded", String(drawer.checked));
    control.setAttribute("aria-label", drawer.checked ? "Close navigation" : "Open navigation");
  };

  control.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      control.click();
    }
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && drawer.checked) {
      drawer.checked = false;
      drawer.dispatchEvent(new Event("change", { bubbles: true }));
      control.focus();
    }
  });
  drawer.addEventListener("change", updateState);
  updateState();
});
