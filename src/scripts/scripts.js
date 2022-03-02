const filenameSpan = document.querySelector("#filename");
const percentSpan = document.querySelector("#percent");
const percentProgress = document.querySelector("#percentProgress");
const loadFileButton = document.querySelector("#loadFileButton");

function startStatusUpdates(event) {
    event.preventDefault();

    loadFileButton.disabled = true;

    const input = event.target.files;

    if (input.files.length) {
        const evtSource = new EventSource("/status");

        evtSource.addEventListener("update", function(event) {
            const strData = event.data.replace(/'/g, '"')
            const objData = JSON.parse(strData);

            filenameSpan.innerHTML = objData.filename;
            percentSpan.innerHTML = `${objData.percent}%`;
            percentProgress.value = objData.percent;
        });

        const data = new FormData();

        for (const file of input.files) {
            data.append('files', file);
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

    } else {
        alert("Select one o more .csv files to process");

        loadFileButton.disabled = false;
    }
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

function getWeeklyAvgTrips(event) {
    event.preventDefault();

    fetch('/weekly_average_trips',{
            method: 'GET'
        }).then(async (response) => {
        const resObj = await response.json();

        showWeeklyAvgTrips(resObj);
    });
}
