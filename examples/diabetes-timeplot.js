function createPlot(document, i, str) {
    
    var newDiv = document.createElement('div');
    newDiv.innerHTML = "<div id='diabetes-" + str + "plot-" + i + "' style='width: 95%;'/>";
    document.body.appendChild(newDiv);
}

function onLoad(days) {
    document = "logbook.html"
    
    var timeplot;
    var eventplot;
    var realNum;
    for (i = 0; i < days; i++) {
        realNum = i + 1;
        var newDiv = document.createElement('div');
        newDiv.innerHTML = "<div id='diabetes-label-" + i + "' class='label'>Day " + realNum + ": </div>";
        document.body.appendChild(newDiv);
        createPlot(document, i, "dex");
        loadDay(timeplot, i, "endpoints/endpoints" + i + ".txt", "dex/dex" + i + ".txt", "ping/ping" + i + ".txt", 
            "events/events" + i + ".xml", "events/hypo_events" + i + ".xml");
        createPlot(document, i, "bolus");
        loadEvents(eventplot, i, "endpoints/endpoints" + i + ".txt", "events/bolus_events" + i + ".xml", 
            "events/carb_events" + i + ".xml", "events/ex_events" + i + ".xml");
        var newDiv = document.createElement('div');
        newDiv.innerHTML = "<br />";
        document.body.appendChild(newDiv);
    }
}

function loadDay(timeplot, i, endpoints, dex, ping, events, hypo) {
    var eventSource0 = new Timeplot.DefaultEventSource();
    var eventSource1 = new Timeplot.DefaultEventSource();
    var eventSource2 = new Timeplot.DefaultEventSource();
    var eventSource3 = new Timeplot.DefaultEventSource();
    var eventSource4 = new Timeplot.DefaultEventSource();

    var transColor = new Timeplot.Color("FFFFFF");
    transColor.transparency(0.01);

    var dexColor = new Timeplot.Color("556270");

    var dexFill = new Timeplot.Color("556270");
    dexFill.transparency(0.4);

    var pingDots = new Timeplot.Color("FF6B6B");

    var eventColor = new Timeplot.Color("C44D58");

    var hypoColor = new Timeplot.Color("4ECDC4");

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
            lineColor: transColor,
            dotColor: transColor
        }),    
       Timeplot.createPlotInfo({
            id: "dex",
            dataSource: new Timeplot.ColumnSource(eventSource1,1),
            valueGeometry: valuegeometry,
            timeGeometry: timegeometry,
            lineColor: dexColor,
            //dotColor: dexColor,
            fillColor: dexFill,
            showValues: true
        }),
        Timeplot.createPlotInfo({
            id: "ping",
            dataSource: new Timeplot.ColumnSource(eventSource2,1),
            valueGeometry: valuegeometry,
            timeGeometry: timegeometry,
            lineColor: transColor,
            dotColor: pingDots,
            //showValues: true
        }),
        Timeplot.createPlotInfo({
            id: "events",
            timeGeometry: timegeometry,
            eventSource: eventSource3,
            lineColor: eventColor
        }),
        Timeplot.createPlotInfo({
            id: "hypo",
            timeGeometry: timegeometry,
            eventSource: eventSource4,
            lineColor: hypoColor
        })
    ];

    timeplot = Timeplot.create(document.getElementById("diabetes-dexplot-" + i), plotInfo);
    timeplot.loadText(endpoints, ",", eventSource0);
    timeplot.loadText(dex, ",", eventSource1);
    timeplot.loadText(ping, ",", eventSource2);
    timeplot.loadXML(events, eventSource3);
    timeplot.loadXML(hypo, eventSource4);
}

function loadEvents(eventplot, i, endpoints, bolus, carbs, ex) {
    var eventSource0 = new Timeplot.DefaultEventSource();
    var eventSource1 = new Timeplot.DefaultEventSource();
    var eventSource2 = new Timeplot.DefaultEventSource();
    var eventSource3 = new Timeplot.DefaultEventSource();

    var transColor = new Timeplot.Color("FFFFFF");
    transColor.transparency(0.01);

    var bolusColor = new Timeplot.Color("556270");
    bolusColor.transparency(0.2);

    var carbColor = new Timeplot.Color("FF6B6B");
    carbColor.transparency(0.4);

    var exColor = new Timeplot.Color("C7F464");
    exColor.transparency(0.4);

    var timegeometry = new Timeplot.DefaultTimeGeometry({
        gridColor: "#DEDEDE",
        axisLabelsPlacement: "top"
    })

    var valuegeometry = new Timeplot.DefaultValueGeometry({
    })

    var plotInfo = [
        Timeplot.createPlotInfo({
            id: "endpoints",
            dataSource: new Timeplot.ColumnSource(eventSource0,1),
            valueGeometry: valuegeometry,
            timeGeometry: timegeometry,
            lineColor: transColor,
            dotColor: transColor
        }),
        Timeplot.createPlotInfo({
            id: "bolus",
            timeGeometry: timegeometry,
            eventSource: eventSource1,
            lineColor: bolusColor
        }),
        Timeplot.createPlotInfo({
            id: "carbs",
            timeGeometry: timegeometry,
            eventSource: eventSource2,
            lineColor: carbColor
        }),
        Timeplot.createPlotInfo({
            id: "ex",
            timeGeometry: timegeometry,
            eventSource: eventSource3,
            lineColor: exColor
        })
    ];

    timeplot = Timeplot.create(document.getElementById("diabetes-bolusplot-" + i), plotInfo);
    timeplot.loadText(endpoints, ",", eventSource0);
    timeplot.loadXML(bolus, eventSource1);
    timeplot.loadXML(carbs, eventSource2);
    timeplot.loadXML(ex, eventSource3);
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