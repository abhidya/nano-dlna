            
              
                /**
 * This function initializes an object that contains all the digit selectors.
 * @returns {Object} - An object that contains all the digit selectors.
 */
function initDigits() {
	const digits = {
		h1: document.querySelector("#h1"),
		h2: document.querySelector("#h2"),
		m1: document.querySelector("#m1"),
		m2: document.querySelector("#m2"),
		s1: document.querySelector("#s1"),
		s2: document.querySelector("#s2"),
		ms1: document.querySelector("#ms1"),
		oh1: document.querySelector("#o-h1"),
		oh2: document.querySelector("#o-h2"),
		om1: document.querySelector("#o-m1"),
		om2: document.querySelector("#o-m2"),
		os1: document.querySelector("#o-s1"),
		os2: document.querySelector("#o-s2"),
		oms1: document.querySelector("#o-ms1"),
	};
	return digits;
}
/**
 * This function sets an object that contains the correct format for the time.
 * @returns {Object} - the time object.
 */
function setTime() {
	let d = new Date();
	let tObj = {
		h: ("0" + d.getHours()).slice(-2),
		m: ("0" + d.getMinutes()).slice(-2),
		s: ("0" + d.getSeconds()).slice(-2),
		ms: ("0" + d.getMilliseconds()).slice(-3),
	};
	return tObj;
}
/**
 * This function updates the 7-segment clock.
 * @param {Object} digits - The digits object.
 */
function updateClock(digits) {
	let t = setTime();
	digits.h1.setAttribute("data-digit", t.h[0]);
	digits.h2.setAttribute("data-digit", t.h[1]);
	digits.m1.setAttribute("data-digit", t.m[0]);
	digits.m2.setAttribute("data-digit", t.m[1]);
	digits.s1.setAttribute("data-digit", t.s[0]);
	digits.s2.setAttribute("data-digit", t.s[1]);
	digits.ms1.setAttribute("data-digit", t.ms[0]);
	digits.oh1.setAttribute("data-digit", t.h[0]);
	digits.oh2.setAttribute("data-digit", t.h[1]);
	digits.om1.setAttribute("data-digit", t.m[0]);
	digits.om2.setAttribute("data-digit", t.m[1]);
	digits.os1.setAttribute("data-digit", t.s[0]);
	digits.os2.setAttribute("data-digit", t.s[1]);
	digits.oms1.setAttribute("data-digit", t.ms[0]);
}
/**
 * This function initializes an object that contains all the control selectors.
 * @returns {Object} - An object that contains all the control selectors.
 */
function initControls() {
	const C = {
		d7s: document.querySelector("#d7s"),
		od7s: document.querySelector("#od-d7s"),
	};
	return C;
}
/*start the clock*/
const digits = initDigits();
const controls = initControls();
Object.keys(controls).forEach(key => {
	controls[key].addEventListener("input", () => {
		document.getElementById(controls[key].value).classList.toggle("hidden");
	});
});
setInterval(() => {
	updateClock(digits);
}, 100);
              
