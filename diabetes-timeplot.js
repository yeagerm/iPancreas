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
        loadDay(timeplot, i, "endpoints/endpoints" + i + ".txt", "dex/dex" + i + ".txt", "ping/ping" + i + ".txt", 
            "events/carb_events" + i + ".xml", "events/_events" + i + ".xml", "events/ex_events" + i + ".xml",
            "events/hypo_events" + i + ".xml");
    }
}

function loadDay(timeplot, i, endpoints, dex, ping, carbs, events, ex, hypo) {
    var eventSource0 = new Timeplot.DefaultEventSource();
    var eventSource1 = new Timeplot.DefaultEventSource();
    var eventSource2 = new Timeplot.DefaultEventSource();
    var eventSource3 = new Timeplot.DefaultEventSource();
    var eventSource4 = new Timeplot.DefaultEventSource();
    var eventSource5 = new Timeplot.DefaultEventSource();
    var eventSource6 = new Timeplot.DefaultEventSource();

    var pingColor = new Timeplot.Color("FFFFFF");
    pingColor.transparency(0.01);

    var dexFill = new Timeplot.Color("615A55");
    dexFill.transparency(0.6);

    var carbColor = new Timeplot.Color("EA2C46");
    carbColor.transparency(0.4);

    var exColor = new Timeplot.Color("1E9D84");
    exColor.transparency(0.4);

    var timegeometry = new Timeplot.DefaultTimeGeometry({
        gridColor: "#DEDEDE",
        axisLabelsPlacement: "top"
    })

    var valuegeometry = new Timeplot.DefaultValueGeometry({
        gridColor: "#000000",
        axisLabelsPlacement: "left",
        min: 25,
        max: 300
    })

    var plotInfo = [
        Timeplot.createPlotInfo({
            id: "endpoints",
            dataSource: new Timeplot.ColumnSource(eventSource0,1),
            valueGeometry: valuegeometry,
            timeGeometry: timegeometry,
            lineColor: pingColor,
            dotColor: pingColor
        }),    
       Timeplot.createPlotInfo({
            id: "dex",
            dataSource: new Timeplot.ColumnSource(eventSource1,1),
            valueGeometry: valuegeometry,
            timeGeometry: timegeometry,
            lineColor: "#615A55",
            //dotColor: "#615A55",
            fillColor: dexFill,
            showValues: true
        }),
        Timeplot.createPlotInfo({
            id: "carbs",
            timeGeometry: timegeometry,
            eventSource: eventSource3,
            lineColor: carbColor
        }),
        Timeplot.createPlotInfo({
            id: "hypo",
            timeGeometry: timegeometry,
            eventSource: eventSource6,
            lineColor: "#46000A"
        }),
        Timeplot.createPlotInfo({
            id: "events",
            timeGeometry: timegeometry,
            eventSource: eventSource4,
            lineColor: "#50D127"
        }),
        Timeplot.createPlotInfo({
            id: "ex",
            timeGeometry: timegeometry,
            eventSource: eventSource5,
            lineColor: exColor
        }),
        Timeplot.createPlotInfo({
            id: "ping",
            dataSource: new Timeplot.ColumnSource(eventSource2,1),
            valueGeometry: valuegeometry,
            timeGeometry: timegeometry,
            lineColor: pingColor,
            dotColor: "#F67D2E",
            showValues: true
        })
    ];

    timeplot = Timeplot.create(document.getElementById("diabetes-timeplot-" + i), plotInfo);
    timeplot.loadText(endpoints, ",", eventSource0);
    timeplot.loadText(dex, ",", eventSource1);
    timeplot.loadText(ping, ",", eventSource2);
    timeplot.loadXML(carbs, eventSource3);
    timeplot.loadXML(events, eventSource4);
    timeplot.loadXML(ex, eventSource5);
    timeplot.loadXML(hypo, eventSource6);
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