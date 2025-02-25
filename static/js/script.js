document.addEventListener("DOMContentLoaded", function () {
    let startTimeInput = document.getElementById("start_time");
    let endTimeInput = document.getElementById("end_time");
    let shiftSelect = document.getElementById("shift");

    // Format tanggal: YYYY-MM-DDTHH:MM
    function formatDateTime(date, hours, minutes) {
        let year = date.getFullYear();
        let month = String(date.getMonth() + 1).padStart(2, '0');
        let day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}T${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    }

    // Cek apakah ada nilai sebelumnya di localStorage
    if (localStorage.getItem("start_time")) {
        startTimeInput.value = localStorage.getItem("start_time");
    } else {
        let now = new Date();
        startTimeInput.value = formatDateTime(now, now.getHours(), now.getMinutes());
    }

    if (localStorage.getItem("end_time")) {
        endTimeInput.value = localStorage.getItem("end_time");
    } else {
        let now = new Date();
        endTimeInput.value = formatDateTime(now, now.getHours(), now.getMinutes());
    }

    // Event listener untuk dropdown shift
    shiftSelect.addEventListener("change", function () {
        let now = new Date();
        let startHour, endHour;
        
        if (this.value === "1") {
            startHour = 8;  endHour = 16;
        } else if (this.value === "2") {
            startHour = 16; endHour = 24;
        } else if (this.value === "3") {
            startHour = 0;  endHour = 8;
        } else {
            return;
        }

        let newStartTime = formatDateTime(now, startHour, 0);
        let newEndTime;

        if (endHour >= 24) {
            let nextDay = new Date(now);
            nextDay.setDate(now.getDate() + 1);
            newEndTime = formatDateTime(nextDay, 0, 0);
        } else {
            newEndTime = formatDateTime(now, endHour, 0);
        }

        startTimeInput.value = newStartTime;
        endTimeInput.value = newEndTime;

        // Simpan nilai di localStorage
        localStorage.setItem("start_time", newStartTime);
        localStorage.setItem("end_time", newEndTime);
    });

    // Simpan perubahan input secara manual ke localStorage jika user mengedit sendiri
    startTimeInput.addEventListener("change", function () {
        localStorage.setItem("start_time", this.value);
    });

    endTimeInput.addEventListener("change", function () {
        localStorage.setItem("end_time", this.value);
    });
});
