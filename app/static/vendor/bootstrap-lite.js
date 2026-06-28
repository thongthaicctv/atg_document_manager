(function () {
  const modalInstances = new WeakMap();

  function removeBackdrop() {
    document.querySelectorAll(".modal-backdrop").forEach((backdrop) => backdrop.remove());
    document.body.classList.remove("modal-open");
  }

  class Modal {
    constructor(element) {
      this.element = element;
      modalInstances.set(element, this);
    }

    show() {
      if (!this.element) {
        return;
      }
      this.element.style.display = "block";
      this.element.removeAttribute("aria-hidden");
      this.element.setAttribute("aria-modal", "true");
      this.element.classList.add("show");
      document.body.classList.add("modal-open");
      if (!document.querySelector(".modal-backdrop")) {
        const backdrop = document.createElement("div");
        backdrop.className = "modal-backdrop show";
        document.body.appendChild(backdrop);
      }
      this.element.dispatchEvent(new Event("shown.bs.modal"));
    }

    hide() {
      if (!this.element) {
        return;
      }
      this.element.classList.remove("show");
      this.element.style.display = "none";
      this.element.setAttribute("aria-hidden", "true");
      this.element.removeAttribute("aria-modal");
      removeBackdrop();
      this.element.dispatchEvent(new Event("hidden.bs.modal"));
    }

    static getOrCreateInstance(element) {
      return modalInstances.get(element) || new Modal(element);
    }
  }

  window.bootstrap = window.bootstrap || {};
  window.bootstrap.Modal = Modal;

  document.addEventListener("click", (event) => {
    const dismissButton = event.target.closest("[data-bs-dismiss='modal']");
    if (dismissButton) {
      const modal = dismissButton.closest(".modal");
      if (modal) {
        Modal.getOrCreateInstance(modal).hide();
      }
      return;
    }

    const collapseButton = event.target.closest("[data-bs-toggle='collapse']");
    if (collapseButton) {
      const targetSelector = collapseButton.getAttribute("data-bs-target") || collapseButton.getAttribute("href");
      if (!targetSelector) {
        return;
      }
      const target = document.querySelector(targetSelector);
      if (!target) {
        return;
      }
      const isShown = target.classList.toggle("show");
      collapseButton.setAttribute("aria-expanded", isShown ? "true" : "false");
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    const openModal = document.querySelector(".modal.show");
    if (openModal) {
      Modal.getOrCreateInstance(openModal).hide();
    }
  });
})();
