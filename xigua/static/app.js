/* XiGua — small, dependency-free enhancements. */
(function () {
  "use strict";

  var root = document.documentElement;
  var THEME_KEY = "xigua-theme";

  /* Theme toggle -------------------------------------------------------- */
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var current = root.dataset.theme;
      if (!current) {
        current = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      }
      var next = current === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch (error) {}
      toggle.setAttribute("aria-label", next === "dark" ? "切换到浅色主题" : "切换到深色主题");
    });
  }

  /* Reading progress --------------------------------------------------- */
  var progress = document.querySelector(".progress-bar");
  if (progress && document.body.classList.contains("page-post")) {
    var updateProgress = function () {
      var scrollable = document.documentElement.scrollHeight - window.innerHeight;
      var ratio = scrollable > 0 ? window.scrollY / scrollable : 0;
      progress.style.transform = "scaleX(" + Math.min(1, Math.max(0, ratio)) + ")";
    };
    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
    updateProgress();
  }

  /* Code block copy buttons -------------------------------------------- */
  document.querySelectorAll(".prose pre").forEach(function (pre) {
    var button = document.createElement("button");
    button.className = "copy-code";
    button.type = "button";
    button.textContent = "复制";
    button.addEventListener("click", function () {
      var code = pre.querySelector("code");
      var text = code ? code.innerText : pre.innerText;
      var done = function () {
        button.textContent = "已复制";
        window.setTimeout(function () {
          button.textContent = "复制";
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {
          button.textContent = "失败";
        });
      } else {
        var area = document.createElement("textarea");
        area.value = text;
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        try {
          document.execCommand("copy");
          done();
        } catch (error) {
          button.textContent = "失败";
        }
        document.body.removeChild(area);
      }
    });
    pre.appendChild(button);
  });

  /* Client-side search on the blog index ------------------------------- */
  var search = document.getElementById("search");
  var list = document.getElementById("post-list");
  if (search && list) {
    var items = Array.prototype.slice.call(list.querySelectorAll(".post-item"));
    var empty = document.getElementById("no-results");

    var filter = function () {
      var query = search.value.trim().toLowerCase();
      var visible = 0;
      items.forEach(function (item) {
        var haystack = (item.dataset.search || item.textContent || "").toLowerCase();
        var match = !query || haystack.indexOf(query) !== -1;
        item.hidden = !match;
        if (match) visible += 1;
      });
      if (empty) empty.hidden = visible !== 0;
    };

    search.addEventListener("input", filter);

    document.addEventListener("keydown", function (event) {
      var target = event.target;
      var typing = target && /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName);
      if (event.key === "/" && !typing) {
        event.preventDefault();
        search.focus();
      } else if (event.key === "Escape" && document.activeElement === search) {
        search.value = "";
        filter();
        search.blur();
      }
    });
  }
})();
