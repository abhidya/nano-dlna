// Gradient Bubbles JavaScript - Mouse tracking for interactive element
window.addEventListener("mousemove", e => {
  const interactable = document.querySelector(".interactive");
  
  if (interactable) {
    const interactableRect = interactable.getBoundingClientRect();
    const x = e.clientX - interactableRect.width / 2;
    const y = e.clientY - interactableRect.height / 2;
    
    const keyframes = {
      transform: `translate(${x}px, ${y}px)`
    };
    
    interactable.animate(keyframes, {
      duration: 800,
      fill: "forwards"
    });
  }
});