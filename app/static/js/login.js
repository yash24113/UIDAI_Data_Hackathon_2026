let loginMethod = "";

// ✅ Aadhaar selected by default on page load
document.addEventListener("DOMContentLoaded", () => {
    selectMethod("aadhaar");
});


function selectMethod(method) {
    loginMethod = method;

    ["aadhaarBox", "mobileBox", "emailBox"].forEach(id =>
        document.getElementById(id).classList.add("d-none")
    );

    document.getElementById(method + "Box").classList.remove("d-none");
}

function showOTPModal() {
    document.getElementById('otpModal').classList.add('show');
    document.getElementById('otp1').focus();
}

const otpInputs = document.querySelectorAll('.otp-input');
otpInputs.forEach((input, index) => {
    input.addEventListener('input', (e) => {
        if (e.target.value.length === 1 && index < 5) {
            otpInputs[index + 1].focus();
        }
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && !e.target.value && index > 0) {
            otpInputs[index - 1].focus();
        }
    });

    // Only allow numbers
    input.addEventListener('keypress', (e) => {
        if (!/[0-9]/.test(e.key)) {
            e.preventDefault();
        }
    });
});

function closeOTPModal() {
    document.getElementById('otpModal').classList.remove('show');
    // Clear OTP inputs
    for (let i = 1; i <= 6; i++) {
        document.getElementById('otp' + i).value = '';
    }
}

function sendAadhaarOTP() {
    const aadhaarInput = document.getElementById("aadhaar").value.trim();

    if (!/^\d{12}$/.test(aadhaarInput)) {
        showMsg("❌ Aadhaar must be 12 digits", "danger");
        return;
    }

    fetch("https://6964c650e8ce952ce1f2f83e.mockapi.io/login")
        .then(res => res.json())
        .then(users => {
            console.log("Fetched users:", users);

            // ✅ Normalize both sides (IMPORTANT)
            const user = users.find(u =>
                String(u.aadhaar).trim() === String(aadhaarInput)
            );

            if (!user) {
                showMsg("❌ Aadhaar not registered", "danger");
                return;
            }

            const phone = String(user.phone || "").trim();

            if (!phone) {
                showMsg("❌ No mobile linked with Aadhaar", "danger");
                return;
            }

            console.log("Matched user:", user);

            // ✅ Send OTP to backend
            fetch("/auth/login/mobile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    phone: phone,
                    name: user.name,
                    email: user.email,
                    aadhaar: user.aadhaar
                })
            })
                .then(res => res.json())
                .then(() => {
                    showMsg(
                        `✅ OTP sent to registered mobile ending ${phone.slice(-4)}`,
                        "success"
                    );
                    showOTPModal();
                })
                .catch(() => {
                    showMsg("❌ Failed to send OTP", "danger");
                });
        })
        .catch(err => {
            console.error(err);
            showMsg("❌ Unable to fetch Aadhaar records", "danger");
        });
}

function sendMobileOTP() {
    let phone = document.getElementById("mobile").value.trim();

    // Normalize phone (optional but recommended)
    if (!phone.startsWith("+")) {
        if (/^\d{10}$/.test(phone)) {
            phone = "+91" + phone;
            document.getElementById("mobile").value = phone;
        } else {
            showMsg("❌ Enter valid 10-digit mobile number", "danger");
            return;
        }
    }

    // 1️⃣ Fetch users from MockAPI
    fetch("https://6964c650e8ce952ce1f2f83e.mockapi.io/login")
        .then(res => res.json())
        .then(users => {
            // ✅ Check if users array is empty
            if (!users || users.length === 0) {
                showMsg("❌ No users found in system", "danger");
                return;
            }

            // 2️⃣ Check mobile exists
            const user = users.find(
                u => String(u.phone).trim() === phone
            );

            if (!user) {
                showMsg("❌ Mobile number not registered", "danger");
                return;
            }

            // 3️⃣ Mobile exists → send OTP
            fetch("/auth/login/mobile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone })
            })
                .then(r => r.json())
                .then(d => {
                    if (d.success) {
                        showMsg(d.message, "success");
                        showOTPModal();
                    } else {
                        showMsg(d.message || "❌ Failed to send OTP", "danger");
                    }
                })
                .catch(() => {
                    showMsg("❌ Failed to send OTP", "danger");
                });
        })
        .catch(() => {
            showMsg("❌ Unable to check mobile records", "danger");
        });
}

async function sendEmailOTP() {
    const emailInput = document.getElementById("email");
    const email = emailInput.value.trim();

    // 1️⃣ Empty check
    if (!email) {
        showMsg("❌ Email is required", "danger");
        return;
    }

    // 2️⃣ Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMsg("❌ Enter a valid email address", "danger");
        return;
    }

    try {
        // 3️⃣ Fetch users
        const res = await fetch("https://6964c650e8ce952ce1f2f83e.mockapi.io/login");
        if (!res.ok) throw new Error("MockAPI error");

        const users = await res.json();

        // 4️⃣ Check email exists
        const user = users.find(
            u => String(u.email).toLowerCase().trim() === email.toLowerCase()
        );

        if (!user) {
            showMsg("❌ Email not registered", "danger");
            return;
        }

        // 5️⃣ Send OTP
        const otpRes = await fetch("/auth/login/email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });

        const otpData = await otpRes.json();

        if (!otpRes.ok || otpData.success === false) {
            throw new Error("OTP failed");
        }

        showMsg("✅ OTP sent to registered email", "success");
        showOTPModal();

    } catch (err) {
        console.error(err);
        showMsg("❌ Something went wrong. Try again.", "danger");
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


function showOtp() {
    document.getElementById("otpBox").classList.remove("d-none");
}

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