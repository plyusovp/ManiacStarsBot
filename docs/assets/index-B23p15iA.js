(function(){const r=document.createElement("link").relList;if(r&&r.supports&&r.supports("modulepreload"))return;for(const t of document.querySelectorAll('link[rel="modulepreload"]'))s(t);new MutationObserver(t=>{for(const o of t)if(o.type==="childList")for(const i of o.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&s(i)}).observe(document,{childList:!0,subtree:!0});function n(t){const o={};return t.integrity&&(o.integrity=t.integrity),t.referrerPolicy&&(o.referrerPolicy=t.referrerPolicy),t.crossOrigin==="use-credentials"?o.credentials="include":t.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function s(t){if(t.ep)return;t.ep=!0;const o=n(t);fetch(t.href,o)}})();function l(e){e.innerHTML=`
        <h1>Games</h1>
        <p>Welcome to the games section. Choose a game to play!</p>
    `}const u=Object.freeze(Object.defineProperty({__proto__:null,init:l},Symbol.toStringTag,{value:"Module"}));function d(e){e.innerHTML=`
        <h1>Referrals</h1>
        <p>Invite your friends and earn rewards.</p>
    `}const f=Object.freeze(Object.defineProperty({__proto__:null,init:d},Symbol.toStringTag,{value:"Module"}));function p(e){e.innerHTML=`
        <h1>Profile</h1>
        <p>View and edit your profile information here.</p>
    `}const g=Object.freeze(Object.defineProperty({__proto__:null,init:p},Symbol.toStringTag,{value:"Module"}));function m(e){e.innerHTML=`
        <h1>Settings</h1>
        <p>Adjust your application settings.</p>
    `}const h=Object.freeze(Object.defineProperty({__proto__:null,init:m},Symbol.toStringTag,{value:"Module"}));function y(e){e.innerHTML=`
        <h1>Taper</h1>
        <p>This is the taper game content.</p>
    `}const b=Object.freeze(Object.defineProperty({__proto__:null,init:y},Symbol.toStringTag,{value:"Module"})),c={"/":u,"/referrals":f,"/profile":g,"/settings":h,"/taper":b},_=e=>{window.location.pathname!==e&&(window.history.pushState({},e,window.location.origin+e),a())},a=async()=>{const e=window.location.pathname,r=c[e]||c["/"],n=document.getElementById("app");n?(await r.init(n),v(e)):console.error("Элемент с id 'app' не найден!")},v=e=>{document.querySelectorAll("nav a").forEach(r=>{r.classList.remove("active"),r.getAttribute("href")===e&&r.classList.add("active")})};window.addEventListener("DOMContentLoaded",()=>{document.body.addEventListener("click",e=>{e.target.matches("[data-link]")&&(e.preventDefault(),_(e.target.getAttribute("href")))}),a()});
