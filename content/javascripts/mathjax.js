/* Configuration precedes the exact-version CDN script in mkdocs.yml. */
(() => {
  if (window.EuvicsMath) return;
  let ready = false;
  let previousRoot;
  const rendered = new WeakSet();
  let queue = Promise.resolve();
  let subscription;
  const report = () => {
    const root = document.querySelector(".md-content__inner");
    if (!root?.querySelector(".arithmatex") || root.querySelector(".equation-status")) return;
    const message = document.createElement("p");
    message.className = "equation-status";
    message.setAttribute("role", "status");
    message.textContent = "Equation rendering is unavailable. The original TeX remains visible; reload to retry.";
    root.prepend(message);
  };
  const render = () => {
    if (!ready) return queue;
    queue = queue.then(async () => {
      const root = document.querySelector(".md-content__inner");
      if (!root) return;
      if (previousRoot && previousRoot !== root) {
        window.MathJax.typesetClear([previousRoot]);
        window.MathJax.texReset();
      }
      previousRoot = root;
      const equations = [...root.querySelectorAll(".arithmatex")].filter(node => !rendered.has(node));
      if (!equations.length) return;
      await window.MathJax.typesetPromise(equations);
      equations.forEach(node => rendered.add(node));
      root.querySelector(".equation-status")?.remove();
    }).catch(report);
    return queue;
  };
  const initialize = () => {
    if (typeof document$ !== "undefined" && !subscription) subscription = document$.subscribe(render);
    render();
  };
  const loadError = event => {
    if (event.target instanceof HTMLScriptElement && event.target.src.includes("/mathjax@3.2.2/")) report();
  };
  window.addEventListener("error", loadError, true);
  window.EuvicsMath = { render, initialize };
  window.MathJax = {
    tex: {
      inlineMath: [["\\(", "\\)"]],
      displayMath: [["\\[", "\\]"]],
      processEscapes: true,
      processEnvironments: true
    },
    options: { ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex" },
    startup: {
      typeset: false,
      pageReady: () => {
        ready = true;
        return render();
      }
    }
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
