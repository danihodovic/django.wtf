document.addEventListener("DOMContentLoaded", function(event) {
  document.querySelectorAll("h1").forEach(el => {
    el.classList.add("text-2xl", "pt-4", "pb-1");
  });

  document.querySelectorAll("p").forEach(el => {
    el.classList.add("py-1");
  });

  document.querySelectorAll(".readme a").forEach(el => {
    el.classList.add("text-blue-400");
  });

  document.querySelectorAll(".codehilite pre").forEach(el => {
    el.classList.add("m-4", "rounded");
  });

  document.querySelectorAll("code").forEach(el => {
    el.classList.add("m-2", "rounded");
  });
});
