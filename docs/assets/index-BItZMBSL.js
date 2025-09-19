(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))o(a);new MutationObserver(a=>{for(const i of a)if(i.type==="childList")for(const p of i.addedNodes)p.tagName==="LINK"&&p.rel==="modulepreload"&&o(p)}).observe(document,{childList:!0,subtree:!0});function n(a){const i={};return a.integrity&&(i.integrity=a.integrity),a.referrerPolicy&&(i.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?i.credentials="include":a.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function o(a){if(a.ep)return;a.ep=!0;const i=n(a);fetch(a.href,i)}})();const V=[{id:"taper",icon:"👆",text:"Taper"},{id:"referrals",icon:"🤝",text:"Referrals"},{id:"games",icon:"🎮",text:"Games"},{id:"profile",icon:"🧑‍🚀",text:"Profile"}],J=(e,t)=>{const n=V.map(o=>`
        <a href="#${o.id}" class="nav-link ${t===o.id?"active":""}">
            <span class="icon">${o.icon}</span>
            <span class="text">${o.text}</span>
        </a>
    `).join("");e.innerHTML=`<nav class="main-nav">${n}</nav>`};let N={},H="en";async function Q(){try{const e=await fetch("./locales/i18n.json");if(!e.ok)throw new Error(`HTTP error! status: ${e.status}`);N=await e.json()}catch(e){console.error("Could not load translations:",e)}}function Z(e){H=e}function c(e){return N[H]?.[e]||e}async function ee(e="en"){Z(e),await Q()}let r,h;const g={tap:null,win:null,lose:null},L=(e,t,n="sine")=>{if(!r)return null;const o=r.sampleRate,a=o*t,i=r.createBuffer(1,a,o),p=i.getChannelData(0);for(let y=0;y<a;y++){const _=y/o;p[y]=Math.sin(e*2*Math.PI*_)*Math.exp(-_*5)}return i},te=()=>{if(!r)try{r=new(window.AudioContext||window.webkitAudioContext),h=r.createGain(),h.gain.value=.5,h.connect(r.destination),g.tap=L(440,.1,"triangle"),g.win=L(880,.2,"sine"),g.lose=L(220,.3,"square"),console.log("Audio initialized successfully.")}catch(e){console.error("Web Audio API is not supported in this browser.",e)}},M=e=>{if(!r||!e||h.gain.value===0){r&&r.state==="suspended"&&r.resume();return}const t=r.createBufferSource();t.buffer=e,t.connect(h),t.start(0)},ne=()=>M(g.tap),B=()=>M(g.win),w=()=>M(g.lose);let P=10,b=50;const oe=`
    <div class="game-container">
        <h2>${c("dice_game_title")}</h2>
        <div class="dice-controls">
            <div class="control-group">
                <label for="bet-amount">${c("bet_amount")}:</label>
                <input type="number" id="bet-amount" value="${P}" min="1">
            </div>
            <div class="control-group">
                <label for="win-chance">${c("win_chance")} (%):</label>
                <input type="range" id="win-chance" min="1" max="99" value="${b}">
                <span id="win-chance-value">${b}%</span>
            </div>
            <button id="roll-dice-button">${c("roll_dice")}</button>
        </div>
        <div class="dice-result">
            <p>${c("result")}: <span id="dice-outcome"></span></p>
        </div>
    </div>
`,q=()=>{const e=document.getElementById("win-chance"),t=document.getElementById("win-chance-value");e&&t&&(t.textContent=`${e.value}%`,b=parseInt(e.value,10))},F=()=>{const e=document.getElementById("bet-amount");P=parseInt(e.value,10);const t=document.getElementById("dice-outcome");if(!t)return;const n=Math.floor(Math.random()*100)+1;n<=b?(t.textContent=`${c("win")}! You rolled ${n}.`,t.style.color="green",B()):(t.textContent=`${c("loss")}! You rolled ${n}.`,t.style.color="red",w())},ae=e=>{e.innerHTML=oe,document.getElementById("win-chance").addEventListener("input",q),document.getElementById("roll-dice-button").addEventListener("click",F)},ce=()=>{const e=document.getElementById("win-chance");e&&e.removeEventListener("input",q);const t=document.getElementById("roll-dice-button");t&&t.removeEventListener("click",F)},ie={id:"dice",init:ae,cleanup:ce},A=["🍒","🍋","🍊","🍉","⭐","🔔","🍀"];let O=10;const se=`
    <div class="game-container">
        <h2>${c("slots_game_title")}</h2>
        <div class="slots-reels">
            <div class="reel" id="reel1"></div>
            <div class="reel" id="reel2"></div>
            <div class="reel" id="reel3"></div>
        </div>
        <div class="slots-controls">
            <div class="control-group">
                <label for="slots-bet-amount">${c("bet_amount")}:</label>
                <input type="number" id="slots-bet-amount" value="${O}" min="1">
            </div>
            <button id="spin-button">${c("spin")}</button>
        </div>
        <div class="slots-result">
            <p id="slots-outcome"></p>
        </div>
    </div>
`,le=()=>{const e=[document.getElementById("reel1"),document.getElementById("reel2"),document.getElementById("reel3")],t=[];return e.forEach((n,o)=>{const a=A[Math.floor(Math.random()*A.length)];t.push(a),n.textContent=a}),t},Y=()=>{const e=document.getElementById("slots-bet-amount");O=parseInt(e.value,10);const t=document.getElementById("slots-outcome");if(!t)return;const n=le();n[0]===n[1]&&n[1]===n[2]?(t.textContent=`${c("win")}! You got three ${n[0]}s.`,t.style.color="green",B()):(t.textContent=`${c("try_again")}`,t.style.color="inherit",w())},re=e=>{e.innerHTML=se,document.getElementById("spin-button").addEventListener("click",Y)},de=()=>{const e=document.getElementById("spin-button");e&&e.removeEventListener("click",Y)},ue={id:"slots",init:re,cleanup:de};let k=10,m=1,f="waiting",E;const me=`
    <div class="game-container">
        <h2>${c("crash_game_title")}</h2>
        <div class="crash-graph">
            <p id="multiplier-display">x1.00</p>
        </div>
        <div class="crash-controls">
            <div class="control-group">
                <label for="crash-bet-amount">${c("bet_amount")}:</label>
                <input type="number" id="crash-bet-amount" value="${k}" min="1">
            </div>
            <button id="crash-button">${c("place_bet")}</button>
        </div>
        <div class="crash-result">
            <p id="crash-outcome"></p>
        </div>
    </div>
`,j=()=>{m=1,f="waiting",document.getElementById("multiplier-display").textContent=`x${m.toFixed(2)}`,document.getElementById("multiplier-display").style.color="white",document.getElementById("crash-button").textContent=c("place_bet"),document.getElementById("crash-button").disabled=!1,document.getElementById("crash-outcome").textContent=""},pe=()=>{f="running",document.getElementById("crash-button").textContent=c("cash_out");const e=1+Math.random()*99;E=setInterval(()=>{m+=.01,document.getElementById("multiplier-display").textContent=`x${m.toFixed(2)}`,m>=e&&(clearInterval(E),f="crashed",document.getElementById("multiplier-display").style.color="red",document.getElementById("crash-button").textContent=c("crashed"),document.getElementById("crash-button").disabled=!0,document.getElementById("crash-outcome").textContent=`${c("crashed_at")} x${m.toFixed(2)}`,w(),setTimeout(j,3e3))},50)},z=()=>{if(f==="waiting")document.getElementById("crash-bet-amount"),k=parseInt(betAmount-input.value,10),pe();else if(f==="running"){clearInterval(E),f="cashed_out";const e=(k*m).toFixed(2);document.getElementById("crash-outcome").textContent=`${c("cashed_out_at")} x${m.toFixed(2)}! ${c("you_won")} ${e}`,document.getElementById("crash-button").disabled=!0,B(),setTimeout(j,3e3)}},ge=e=>{e.innerHTML=me,document.getElementById("crash-button").addEventListener("click",z)},fe=()=>{clearInterval(E);const e=document.getElementById("crash-button");e&&e.removeEventListener("click",z)},ve={id:"crash",init:ge,cleanup:fe};let D=10;const he=`
    <div class="game-container">
        <h2>${c("coin_flip_game_title")}</h2>
        <div class="coin-flipper">
            <div id="coin" class="">
                <div class="heads">H</div>
                <div class="tails">T</div>
            </div>
        </div>
        <div class="coin-controls">
             <div class="control-group">
                <label for="coin-bet-amount">${c("bet_amount")}:</label>
                <input type="number" id="coin-bet-amount" value="${D}" min="1">
            </div>
            <div class="control-group">
                <button class="choice-button" data-choice="heads">${c("heads")}</button>
                <button class="choice-button" data-choice="tails">${c("tails")}</button>
            </div>
        </div>
        <div class="coin-result">
            <p id="coin-outcome"></p>
        </div>
    </div>
`,W=e=>{const t=document.getElementById("coin"),n=document.getElementById("coin-outcome"),o=document.getElementById("coin-bet-amount");D=parseInt(o.value,10),document.querySelectorAll(".choice-button").forEach(i=>i.disabled=!0),n.textContent="",t.className="";const a=Math.random()<.5?"heads":"tails";requestAnimationFrame(()=>{t.classList.add("flipping"),setTimeout(()=>{t.classList.remove("flipping"),t.classList.add(a==="heads"?"is-heads":"is-tails"),e===a?(n.textContent=`${c("win")}! It was ${c(a)}.`,n.style.color="green",B()):(n.textContent=`${c("loss")}! It was ${c(a)}.`,n.style.color="red",w()),document.querySelectorAll(".choice-button").forEach(i=>i.disabled=!1)},1e3)})},ye=e=>{e.innerHTML=he,document.querySelectorAll(".choice-button").forEach(t=>{t.addEventListener("click",n=>W(n.target.dataset.choice))})},be=()=>{document.querySelectorAll(".choice-button").forEach(e=>{e.removeEventListener("click",t=>W(t.target.dataset.choice))})},Ee={id:"coin",init:ye,cleanup:be},d={dice:ie,slots:ue,crash:ve,coin:Ee};let l=null;const X=`
    <div class="screen">
        <div class="games-selection">
            ${Object.keys(d).map(e=>`<button class="game-selector" data-game="${e}">${c(e)}</button>`).join("")}
        </div>
        <div id="game-container"></div>
    </div>
`,R=e=>{const t=document.getElementById("game-container");t&&(l&&d[l]&&d[l].cleanup&&d[l].cleanup(),l=e,d[l]&&d[l].init&&d[l].init(t))},$e=e=>{e.innerHTML=X,document.querySelectorAll(".game-selector").forEach(o=>{o.addEventListener("click",a=>{const i=a.target.dataset.game;R(i)})});const n=Object.keys(d)[0];n&&R(n)},xe=()=>{l&&d[l]&&d[l].cleanup&&d[l].cleanup(),l=null},Ie={id:"games",template:X,init:$e,cleanup:xe},s={user:{}},Be=`
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(5px);
}
.modal-content {
    background-color: #2c2c2c;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    color: white;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    max-width: 85%;
    border: 1px solid #444;
}
.modal-content p {
    margin: 0;
    font-size: 1.1em;
}
.modal-close-btn {
    margin-top: 20px;
    padding: 10px 20px;
    border: none;
    background-color: #555;
    color: white;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
}
.modal-close-btn:hover {
    background-color: #666;
}
`,we=()=>{if(!document.getElementById("modal-styles")){const e=document.createElement("style");e.id="modal-styles",e.type="text/css",e.innerText=Be,document.head.appendChild(e)}},G=e=>{if(we(),document.querySelector(".modal-overlay"))return;const t=document.createElement("div");t.className="modal-overlay";const n=document.createElement("div");n.className="modal-content";const o=document.createElement("p");o.textContent=e;const a=document.createElement("button");a.textContent="OK",a.className="modal-close-btn";const i=()=>{document.body.contains(t)&&document.body.removeChild(t)};a.onclick=i,t.onclick=p=>{p.target===t&&i()},n.appendChild(o),n.appendChild(a),t.appendChild(n),document.body.appendChild(t)},Ce=e=>`
    <div class="screen">
        <div class="referral-card">
            <h2>Your Referral Link</h2>
            <p>Share this link with your friends. You'll get a bonus for each friend who joins!</p>
            <div class="referral-link-container">
                <input type="text" value="${e}" readonly id="referral-link-input">
                <button id="copy-referral-link">Copy</button>
            </div>
        </div>
    </div>
`,Le=()=>{const e=document.getElementById("referral-link-input");if(e&&e.value){e.select(),e.setSelectionRange(0,99999);try{document.execCommand("copy"),G("Referral link copied!")}catch(t){console.error("Fallback copy failed: ",t),G("Could not copy link.")}}},ke=e=>{const t=s.user?s.user.id:"your_unique_id",n=`${window.location.origin}${window.location.pathname}?ref=${t}`;e.innerHTML=Ce(n);const o=document.getElementById("copy-referral-link");o&&o.addEventListener("click",Le)},Te=()=>{},Me={id:"referrals",init:ke,cleanup:Te},u={},C={on(e,t){u[e]||(u[e]=[]),u[e].push(t)},emit(e,t){u[e]&&u[e].forEach(n=>n(t))},off(e,t){u[e]&&(u[e]=u[e].filter(n=>n!==t))}},Se=`
<div id="taper-screen" class="screen">
    <div class="taper-container">
        <div class="taper-header">
            <h1 class="balance-label">Your Balance</h1>
            <div class="balance-container">
                <span id="taper-balance">0</span>
            </div>
        </div>
        <div class="taper-circle-container">
            <div id="taper-circle" class="taper-circle">
                <img src="./assets/logo.png" alt="Maniac Stars Logo">
            </div>
        </div>
        <div class="taper-stats">
            <div class="stat">
                <p>Energy</p>
                <div>
                    <span id="taper-energy">1000</span>/<span id="taper-max-energy">1000</span>
                </div>
            </div>
        </div>
        <div id="floating-numbers-container"></div>
    </div>
</div>
`;let v=null;const $=()=>{const e=document.getElementById("taper-balance");e&&(e.textContent=Math.floor(s.balance))},S=()=>{const e=document.getElementById("taper-energy"),t=document.getElementById("taper-max-energy");e&&t&&(e.textContent=s.energy,t.textContent=s.maxEnergy)},_e=(e,t)=>{const n=document.getElementById("floating-numbers-container");if(!n)return;const o=document.createElement("div");o.className="floating-number",o.textContent=`+${s.perTap}`,o.style.left=`${e}px`,o.style.top=`${t}px`,n.appendChild(o),requestAnimationFrame(()=>{o.style.transform="translateY(-100px)",o.style.opacity="0"}),setTimeout(()=>{n.contains(o)&&n.removeChild(o)},1e3)},x=e=>{if(e.preventDefault(),s.energy>=s.perTap){s.balance+=s.perTap,s.energy-=s.perTap,$(),S();const t=e.touches?e.touches[0].clientX:e.clientX,n=e.touches?e.touches[0].clientY:e.clientY;_e(t,n);const o=e.currentTarget;o.style.transform="scale(0.95)",setTimeout(()=>{o.style.transform="scale(1)"},100)}},Ae=()=>{v&&clearInterval(v),v=setInterval(()=>{s.energy<s.maxEnergy&&(s.energy=Math.min(s.maxEnergy,s.energy+s.energyRegenRate),S())},1e3)},Re=e=>{e.innerHTML=Se;const t=document.getElementById("taper-circle");t&&(t.addEventListener("click",x),t.addEventListener("touchstart",x,{passive:!1})),$(),S(),Ae(),C.on("state:updateBalance",$)},Ge=()=>{const e=document.getElementById("taper-circle");e&&(e.removeEventListener("click",x),e.removeEventListener("touchstart",x)),v&&(clearInterval(v),v=null),C.off("state:updateBalance",$)},Ne={id:"taper",init:Re,cleanup:Ge},He=`
<div id="profile-screen" class="screen">
    <div class="profile-container">
        <div class="profile-header">
            <img src="./assets/logo.png" alt="User Avatar" class="avatar">
            <h1 id="username"></h1>
        </div>
        <div class="profile-stats">
            <div class="stat">
                <p>Balance</p>
                <span id="profile-balance">0</span>
            </div>
            <div class="stat">
                <p>Total Earned</p>
                <span id="total-earned">0</span>
            </div>
        </div>
        <div class="profile-actions">
            <button id="logout-button">Logout</button>
        </div>
    </div>
</div>
`,T=()=>{const e=document.getElementById("username"),t=document.getElementById("profile-balance"),n=document.getElementById("total-earned");e&&(e.textContent=s.user?s.user.username:"Guest"),t&&(t.textContent=Math.floor(s.balance)),n&&(n.textContent=Math.floor(s.totalEarned||0))},K=()=>{console.log("User logged out")},Pe=e=>{e.innerHTML=He;const t=document.getElementById("logout-button");t&&t.addEventListener("click",K),T(),C.on("state:updateBalance",T)},qe=()=>{const e=document.getElementById("logout-button");e&&e.removeEventListener("click",K),C.off("state:updateBalance",T)},Fe={id:"profile",init:Pe,cleanup:qe},Oe={GamesScreen:Ie,referralsScreen:Me,taperScreen:Ne,profileScreen:Fe},U=()=>window.location.pathname||"/games",I=(e,t=!1)=>{const n=document.getElementById("screen-container");if(!n){console.error("Screen container #screen-container not found!");return}const o=Oe.find(a=>a.path.includes(":")?new RegExp(`^${a.path.replace(/:\w+/g,"([^/]+)")}$`).test(e):a.path===e);if(o){for(t?window.history.replaceState({},"",e):window.history.pushState({},"",e);n.firstChild;)n.removeChild(n.firstChild);const a=o.component();n.appendChild(a),document.dispatchEvent(new CustomEvent("navigate",{detail:{path:e}}))}else console.error(`No route found for path: ${e}`),e!=="/games"&&I("/games")};window.addEventListener("popstate",()=>{const e=U();I(e,!0)});function Ye(){ee().then(()=>{J(),I(U())}),document.body.addEventListener("click",t=>{te(),t.target.closest("button, a")&&ne()});const e=document.getElementById("bottom-nav");e?e.addEventListener("click",t=>{const n=t.target.closest(".nav-btn");n&&n.dataset.route&&I(n.dataset.route)}):console.error("Navigation container #bottom-nav not found during initialization!")}document.addEventListener("DOMContentLoaded",Ye);
