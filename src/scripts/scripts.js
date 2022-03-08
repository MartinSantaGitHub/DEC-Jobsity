const filenameSpan = document.querySelector("#filename");
const percentSpan = document.querySelector("#percent");
const percentProgress = document.querySelector("#percentProgress");
const loadFileButton = document.querySelector("#loadFileButton");

function startStatusUpdates(event) {
    event.preventDefault();

    loadFileButton.disabled = true;

    const input = event.target.files;
    const evtSource = new EventSource("/status");

    evtSource.addEventListener("update", function (event) {
        const strData = event.data.replace(/'/g, '"')
        const objData = JSON.parse(strData);

        filenameSpan.innerHTML = objData.filename;
        percentSpan.innerHTML = `${objData.percent}%`;
        percentProgress.value = objData.percent;
    });

    let data = {};

    if (input.files.length) {
        data = new FormData();

        for (const file of input.files) {
            data.append('files', file);
        }
    }

    fetch('/uploadfiles', {
        method: 'POST',
        body: data
    }).then(async (response) => {
        input.value = ""
        loadFileButton.disabled = false;
        percentProgress.value = 0;
        filenameSpan.innerHTML = "";
        percentSpan.innerHTML = "";
        evtSource.close();
        alert(await response.json());
    });
}

function showWeeklyAvgTrips(resObj) {
    const message = resObj.message

    if (!message) {
        const tableBody = document.querySelector("#tableBody");

        tableBody.innerHTML = "";

        resObj.data.forEach(elem => {
            tableBody.innerHTML += `<tr><td>${elem.region}</td><td>${elem.weekly_avg_trips}</td></tr>`
        });
    } else {
        alert(message);
    }
}

function getWeeklyAvgTripsByRegion(event) {
    event.preventDefault();

    fetch('/weekly_average_trips_by_region', {
        method: 'GET'
    }).then(async (response) => {
        const resObj = await response.json();

        showWeeklyAvgTrips(resObj);
    });
}

function getWeeklyAvgTripsByBoundingBox(event) {
    event.preventDefault();

    const boundingBox = {
        x_a: document.querySelector("#x_a").value,
        y_a: document.querySelector("#y_a").value,
        x_b: document.querySelector("#x_b").value,
        y_b: document.querySelector("#y_b").value
    }

    fetch('/get_weekly_average_trips_by_bounding_box', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(boundingBox)
    }).then(async (response) => {
        console.log(response);
        const resObj = await response.json();

        document.querySelector("#bb_result").value = resObj.data;
    });
}
