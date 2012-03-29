function createPlot(document, i) {
    var realNum = i + 1;
    var newDiv = document.createElement('div');
    // TODO: open file and read info to put in label
    newDiv.innerHTML = "<div id='diabetes-label-" + i + "' class='label'>Day " + realNum + ": </div>\
                        <div id='diabetes-timeplot-" + i + "' style='width: 95%;'/>"
    document.body.appendChild(newDiv);
}

function onLoad(days) {
    document = "logbook.html"
    var timeplot;
    for (i = 0; i < days; i++) {
        createPlot(document, i);
        loadDay(timeplot, i, "dex/dex" + i + ".txt", "ping/ping" + i + ".txt");
    }
}

function loadDay(timeplot, i, dex, ping) {
    var eventSource = new Timeplot.DefaultEventSource();
    var eventSource2 = new Timeplot.DefaultEventSource();

    var timegeometry = new Timeplot.DefaultTimeGeometry({
        gridColor: "#000000",
        axisLabelsPlacement: "top",
    })

    var valuegeometry = new Timeplot.DefaultValueGeometry({
        gridColor: "#000000",
        axisLabelsPlacement: "left",
        min: 25,
        max: 300
    })

    var plotInfo = [
        Timeplot.createPlotInfo({
            id: "plot2",
            dataSource: new Timeplot.ColumnSource(eventSource2,1),
            valueGeometry: valuegeometry,
            timeGeometry: timegeometry,
            // secret to getting a "transparent" line for a set of data is to plot it *first*
            lineColor: "#FFFFFF",
            dotColor: "#0000FF"
        }),
	Timeplot.createPlotInfo({
	    id: "plot1",
	    dataSource: new Timeplot.ColumnSource(eventSource,1),
	    // defines upper and lower bounds for graph
	    valueGeometry: valuegeometry,
	    timeGeometry: timegeometry,
            dotColor: "#FF0000",
	    fillColor: "#cc8080",
            showValues: true
	}),
        Timeplot.createPlotInfo({
            id: "plot3",
            timeGeometry: timegeometry,
            eventSource: eventSource2,
            lineColor: "#03212E",
        })
    ];

    timeplot = Timeplot.create(document.getElementById("diabetes-timeplot-" + i), plotInfo);
    timeplot.loadText(dex, ",", eventSource);
    timeplot.loadText(ping, ",", eventSource2);
    //timeplot.loadXML(events, eventSource2);
}

var resizeTimerID = null;
function onResize() {
    if (resizeTimerID == null) {
        resizeTimerID = window.setTimeout(function() {
            resizeTimerID = null;
            timeplot.repaint();
        }, 100);
    }
}

// Local Variables:
// indent-tabs-mode: nil
// End: