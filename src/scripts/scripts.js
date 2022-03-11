const filenameSpan = document.querySelector("#filename");
const percentSpan = document.querySelector("#percent");
const percentProgress = document.querySelector("#percentProgress");
const loadFileButton = document.querySelector("#loadFileButton");

function updateProgress(event) {
    const strData = event.data.replace(/'/g, '"')
    const objData = JSON.parse(strData);

    filenameSpan.innerHTML = objData.filename;
    percentSpan.innerHTML = `${objData.percent}%`;
    percentProgress.value = objData.percent;
}

function uploadFiles(inputFile, data, evtSource, userId) {
    fetch(`/uploadfiles/?user_id=${userId}`, {
        method: 'POST',
        body: data
    }).then(async (response) => {
        inputFile.value = ""
        loadFileButton.disabled = false;
        percentProgress.value = 0;
        filenameSpan.innerHTML = "";
        percentSpan.innerHTML = "";
        evtSource.close();
        alert(await response.json());
    });
}

function startStatusUpdates(event) {
    event.preventDefault();

    loadFileButton.disabled = true;

    const userId = parseFloat(document.querySelector("#user_id").value);
    const inputFile = event.target.files;
    const evtSource = new EventSource(`/status/?user_id=${userId}`);

    evtSource.addEventListener("update", updateProgress);

    let data = {};

    if (inputFile.files.length) {
        data = new FormData();

        for (const file of inputFile.files) {
            data.append('files', file);
        }
    }

    evtSource.onopen = uploadFiles(inputFile, data, evtSource, userId);
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
