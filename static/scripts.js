document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;

    links.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('bg-sky-700', 'text-white');
        }
    });
});

async function getCategory(type) {
    var response = await fetch("getCategory?type=" + type.value)
    var types = await response.json()
    var categories = document.querySelector('#category')
    categories.innerHTML = ''
    const initOption = document.createElement('option')
    initOption.value = ''
    initOption.textContent = "Please Select Category *"
    categories.appendChild(initOption)
    types.forEach(type => {
        var newOption = document.createElement('option')
        newOption.value = type
        newOption.textContent = type
        categories.appendChild(newOption)
    })
}

function changePeriod(type) {
    console.log(type.value)
    var from = document.querySelector('#fromPeriod')
    var to = document.querySelector('#toPeriod')
    var fromYear = document.querySelector('#fromYear')
    var toYear = document.querySelector('#toYear')
    if (type.value == 'Weekly') {
        from.type = 'week'
        to.type = 'week'
        from.hidden = false
        to.hidden = false
        from.required = true
        to.required = true
        fromYear.hidden = true
        toYear.hidden = true
    } else if (type.value == 'Monthly') {
        from.type = 'month'
        to.type = 'month'
        from.hidden = false
        to.hidden = false
        from.required = true
        to.required = true
        fromYear.hidden = true
        toYear.hidden = true
    } else {
        from.hidden = true
        to.hidden = true
        from.required = false
        to.required = false
        fromYear.hidden = false
        toYear.hidden = false
        const currentYear = new Date().getFullYear();
        const startYear = 1990;
        const endYear = currentYear + 20;
        for (let year = startYear; year <= endYear; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            fromYear.appendChild(option);
        }
        for (let year = startYear; year <= endYear; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            toYear.appendChild(option);
        }
    }
}

function changePeriodT(type) {
    console.log(type.value)
    var date = document.querySelector('#date')
    var dateY = document.querySelector('#dateY')
    if (type.value == 'Daily') {
        date.type = 'date'
        date.hidden = false
        date.required = true
        dateY.hidden = true
    } else if (type.value == 'Weekly') {
        date.type = 'week'
        date.hidden = false
        date.required = true
        dateY.hidden = true
    } else if (type.value == 'Monthly') {
        date.type = 'month'
        date.hidden = false
        date.required = true
        dateY.hidden = true
    } else {
        date.hidden = true
        date.required = false
        dateY.hidden = false
        const currentYear = new Date().getFullYear();
        const startYear = 1990;
        const endYear = currentYear + 20;
        for (let year = startYear; year <= endYear; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            dateY.appendChild(option);
        }
    }
}

async function loadNotifications() {
    let res = await fetch("/getNotifications")
    let data = await res.json()
    var countElm = document.getElementById("notificationCount")
    var dropdown = document.getElementById("notificationDropdown")
    count = 0
    dropdown.innerHTML = ''
    data.forEach(n => {
        dropdown.innerHTML += `<a href='/getAll${n.module}' class='grid-cols-2 gap-2 flex justify-around ${n.read ? '' : 'font-bold'}'
        onclick='markRead(${n.id})'>
        <span class="block px-2 py-2 text-sm text-gray-700
        focus:bg-gray-100 focus:outline-none">${n.message}</span>
        <span class="block px-2 py-2 text-sm text-gray-700
        focus:bg-gray-100 focus:outline-none">${n.datestamp}</span></a>`;
        n.read ? '' : count++
    });
    countElm.innerText = count
}

function toggleNotifications() {
    var countElm = document.getElementById("notificationCount")
    let dropdown = document.querySelector("#notificationDropdown")
    dropdown.hidden = !dropdown.hidden;
    countElm.innerText = 0
}

async function markRead(id) {
    console.log(id)
    let res = await fetch("/markReadNotification?id=" + id)
}

loadNotifications()

function calculateDueDate(countInput) {
    const start_date = new Date(document.querySelector("#start_date").value);
    const type = document.querySelector("#frequency").value;
    const next_due = document.querySelector("#next_due");
    let count = parseInt(countInput.value, 10);
    if (isNaN(count) || count < 1) {
        alert("Invalid count");
        return;
    }
    const limits = {
        Weekly: 3,
        Monthly: 11,
        Yearly: 10
    };
    if (count > limits[type]) {
        alert("Invalid count");
        return;
    }
    let next = new Date(start_date);
    if (type === 'Weekly') {
        next.setDate(next.getDate() + count * 7);
    } else if (type === 'Monthly') {
        next.setMonth(next.getMonth() + count);
    } else if (type === 'Yearly') {
        next.setFullYear(next.getFullYear() + count);
    }
    const year = next.getFullYear();
    const month = String(next.getMonth() + 1).padStart(2, '0');
    const day = String(next.getDate()).padStart(2, '0');

    next_due.value = `${year}-${month}-${day}`;
}

function previewImage(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = e => {
            document.getElementById('profilePreview').src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

function writeProfile() {
    var name = document.querySelector("#prUsername")
    var mail = document.querySelector("#prEmail")
    var contact = document.querySelector("#prContact_no")
    var saveBtn = document.querySelector("#saveBtn")
    name.readOnly = false
    mail.readOnly = false
    contact.readOnly = false
    saveBtn.hidden = false
}

async function saveData() {
    var name = document.querySelector("#prUsername")
    var mail = document.querySelector("#prEmail")
    var contact = document.querySelector("#prContact_no")
    var profileImage = document.querySelector("#prImage")
    var saveBtn = document.querySelector("#saveBtn")
    var data = {
        name: name.value,
        mail: mail.value,
        contact: contact.value,
        profileImage: profileImage.value
    }
    let res = await fetch("/profile",
        {
            method: 'post',
            headers: { 'Content-type': 'application/json' },
            body: JSON.stringify(data)
        })
}

function writePassword() {
    var div = document.querySelector("#password_div")
    div.hidden = false
}

async function updatePass() {
    var curr = document.querySelector("#curr")
    var newPass = document.querySelector("#newPass")
    var newCon = document.querySelector("#newCon")
    var data = {
        curr: curr.value,
        newPass: newPass.value,
        newCon: newCon.value
    }
    console.log(data)
    let res = await fetch("/passwordReset",
        {
            method: 'post',
            headers: { 'Content-type': 'application/json' },
            body: JSON.stringify(data)
        })
}
