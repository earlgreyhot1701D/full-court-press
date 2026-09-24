/* Full Court Press . one small vanilla JS file. No framework, no build.
   Rules (guardrails): textContent only, never innerHTML, no eval, no new
   Function. Browser storage only for the visitor's chosen team, in try/catch.
   Every fetch is wrapped in try/catch. The site works fully with JS off; this
   only adds the team-picker convenience and remembers the choice. */
(function () {
  "use strict";

  var STORAGE_KEY = "fcp.team";

  function readTeam() {
    try {
      return window.localStorage.getItem(STORAGE_KEY) || "";
    } catch (e) {
      return "";
    }
  }

  function writeTeam(abbr) {
    try {
      if (abbr) {
        window.localStorage.setItem(STORAGE_KEY, abbr);
      } else {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    } catch (e) {
      /* storage unavailable: the site still works, we just do not remember */
    }
  }

  /* Team picker on the index: pressing a team filters the visible cards and
     remembers the choice. Filtering is presentational only; all cards remain in
     the server-rendered HTML so the no-JS experience is the whole slate. */
  function wireTeamPicker() {
    var nav = document.querySelector("nav.teams.index");
    if (!nav) { return; }
    var buttons = nav.querySelectorAll("button[data-team]");

    function apply(abbr) {
      for (var i = 0; i < buttons.length; i++) {
        buttons[i].setAttribute("aria-pressed", buttons[i].getAttribute("data-team") === abbr ? "true" : "false");
      }
      /* no destructive DOM: we toggle a class, never rebuild markup */
      var cards = document.querySelectorAll(".card");
      for (var j = 0; j < cards.length; j++) {
        var teams = cards[j].getAttribute("data-teams") || "";
        var show = !abbr || teams.split(" ").indexOf(abbr) !== -1;
        cards[j].style.display = show ? "" : "none";
      }
    }

    for (var k = 0; k < buttons.length; k++) {
      buttons[k].addEventListener("click", function (ev) {
        var abbr = ev.currentTarget.getAttribute("data-team") || "";
        writeTeam(abbr);
        apply(abbr);
      });
    }

    var saved = readTeam();
    if (saved) { apply(saved); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireTeamPicker);
  } else {
    wireTeamPicker();
  }
})();
