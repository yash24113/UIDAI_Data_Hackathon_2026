function toggleOtpMethod() {
    const method = document.getElementById("otpMethod").value;
    document.getElementById("sendMobileOtpBtn").classList.add("d-none");
    document.getElementById("sendEmailOtpBtn").classList.add("d-none");

    if (method === "mobile") {
        document.getElementById("sendMobileOtpBtn").classList.remove("d-none");
    }
    if (method === "email") {
        document.getElementById("sendEmailOtpBtn").classList.remove("d-none");
    }
}

function validateCommonFields() {
    let name = nameEl.value.trim();
    let email = emailEl.value.trim();
    let mobile = mobileEl.value.trim();
    let aadhaar = aadhaarEl.value.trim();

    // -------------------------
    // Name validation
    // -------------------------
    if (!name) {
        showMsg("❌ Name is required", "danger");
        return false;
    }

    // -------------------------
    // Email regex validation
    // -------------------------
    const emailRegex = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;
    // If you want ANY email, use:
    // const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(email)) {
        showMsg("❌ Please enter a valid Gmail address", "danger");
        return false;
    }

    // -------------------------
    // Mobile auto-format (+91)
    // -------------------------
    mobile = mobile.replace(/\s+/g, "");

    if (!mobile.startsWith("+")) {
        if (/^\d{10}$/.test(mobile)) {
            mobile = "+91" + mobile;
            mobileEl.value = mobile; // update input
        } else {
            showMsg("❌ Enter a valid 10-digit mobile number", "danger");
            return false;
        }
    }

    if (!/^\+91\d{10}$/.test(mobile)) {
        showMsg("❌ Mobile must be in format +911234567890", "danger");
        return false;
    }

    // -------------------------
    // Aadhaar validation
    // -------------------------
    if (!/^\d{12}$/.test(aadhaar)) {
        showMsg("❌ Aadhaar must be 12 digits", "danger");
        return false;
    }

    return true;
}

function showOTPModal() {
    document.getElementById('otpModal').classList.add('show');
    document.getElementById('otp1').focus();
}

async function sendMobileOTP() {
    if (!validateCommonFields()) return;

    try {
        const response = await fetch("/auth/send-mobile-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(getPayload())
        });

        const data = await response.json();

        if (data.success) {
            showMsg(data.message, "success");
            showOTPModal();
        } else {
            showMsg(data.message, "danger");
        }
    } catch (error) {
        console.error("Error:", error);
        showMsg("❌ Failed to send OTP", "danger");
    }
}

async function sendEmailOTP() {
    if (!validateCommonFields()) return;

    try {
        const response = await fetch("/auth/send-email-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(getPayload())
        });

        const data = await response.json();

        if (data.success) {
            showMsg(data.message, "success");
            showOTPModal();
        } else {
            showMsg(data.message, "danger");
        }
    } catch (error) {
        console.error("Error:", error);
        showMsg("❌ Failed to send OTP", "danger");
    }
}

function verifyOTP() {
    const otp = [...document.querySelectorAll('.otp-input')]
        .map(input => input.value)
        .join('');

    if (otp.length !== 6) {
        showMsg("❌ Please enter complete OTP", "danger");
        return;
    }

    fetch("/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ otp })
    })
        .then(r => r.json())
        .then(d => {
            if (d.success) {
                localStorage.setItem("user", JSON.stringify(d.user));
                window.location.href = "/dashboard";
            } else {
                showMsg(d.message, "danger");
            }
        })
        .catch(() => {
            showMsg("❌ OTP verification failed", "danger");
        });
}

function closeOTPModal() {
    document.getElementById('otpModal').classList.remove('show');
    // Clear OTP inputs
    document.querySelectorAll('.otp-input').forEach(input => input.value = '');
}

function getPayload() {
    return {
        name: nameEl.value.trim(),
        email: emailEl.value.trim(),
        phone: mobileEl.value.trim(),
        aadhaar: aadhaarEl.value.trim()
    };
}

function showOtpBox() {
    document.getElementById("otpBox").classList.remove("d-none");
}

const nameEl = document.getElementById("name");
const emailEl = document.getElementById("email");
const mobileEl = document.getElementById("mobile");
const aadhaarEl = document.getElementById("aadhaar");

function showMsg(message, type) {
    const msgEl = document.getElementById("msg");
    const iconEl = msgEl.querySelector(".msg-icon");
    const contentEl = msgEl.querySelector(".msg-content");

    // Set content
    contentEl.textContent = message;

    // Remove all type classes
    msgEl.className = "";

    // Add show and type classes
    msgEl.classList.add("show", `msg-${type}`);

    // Set icon based on type
    const icons = {
        success: "fas fa-check-circle",
        danger: "fas fa-exclamation-circle",
        info: "fas fa-info-circle",
        warning: "fas fa-exclamation-triangle",
    };

    iconEl.className = `msg-icon ${icons[type] || icons.info}`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        closeMsg();
    }, 5000);
}

function closeMsg() {
    const msgEl = document.getElementById("msg");
    msgEl.classList.remove("show");
}