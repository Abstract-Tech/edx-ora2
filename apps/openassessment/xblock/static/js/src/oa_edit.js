/* JavaScript for Studio editing view of Open Assessment XBlock */


/* Namespace for open assessment */
if (typeof OpenAssessment == "undefined" || !OpenAssessment) {
    OpenAssessment = {};
}


/**
Interface for editing UI in Studio.
The constructor initializes the DOM for editing.

Args:
    runtime (Runtime): an XBlock runtime instance.
    element (DOM element): The DOM element representing this XBlock.
    server (OpenAssessment.Server): The interface to the XBlock server.

Returns:
    OpenAssessment.StudioUI
**/
OpenAssessment.StudioUI = function(runtime, element, server) {
    this.runtime = runtime;
    this.server = server;

    // Initialize the code box
    this.codeBox = CodeMirror.fromTextArea(
        $(element).find('.openassessment-editor').first().get(0),
        {mode: "xml", lineNumbers: true, lineWrapping: true}
    );

    // Install click handlers
    var ui = this;
    $(element).find('.openassessment-save-button').click(
        function(eventData) {
            ui.save();
    });

    $(element).find('.openassessment-cancel-button').click(
        function(eventData) {
            ui.cancel();
    });
};


OpenAssessment.StudioUI.prototype = {

    /**
    Load the XBlock XML definition from the server and display it in the UI.
    **/
    load: function() {
        var ui = this;
        this.server.loadXml().done(
            function(xml) {
                ui.codeBox.setValue(xml);
            }).fail(function(msg) {
                ui.showError(msg);
            }
        );
    },

    /**
    Save the updated XML definition to the server.
    **/
    save: function() {
        // Notify the client-side runtime that we are starting
        // to save so it can show the "Saving..." notification
        this.runtime.notify('save', {state: 'start'});

        // Send the updated XML to the server
        var xml = this.codeBox.getValue();
        var ui = this;
        this.server.updateXml(xml).done(function() {
            // Notify the client-side runtime that we finished saving
            // so it can hide the "Saving..." notification.
            ui.runtime.notify('save', {state: 'end'});

            // Reload the XML definition in the editor
            ui.load();
        }).fail(function(msg) {
            ui.showError(msg);
        });
    },

    /**
    Cancel editing.
    **/
    cancel: function() {
        // Notify the client-side runtime so it will close the editing modal.
        this.runtime.notify('cancel', {});
    },

    /**
    Display an error message to the user.

    Args:
        errorMsg (string): The error message to display.
    **/
    showError: function(errorMsg) {
        this.runtime.notify('error', {msg: errorMsg});
    }
};


/* XBlock entry point for Studio view */
function OpenAssessmentEditor(runtime, element) {

    /**
    Initialize the editing interface on page load.
    **/
    $(function($) {
        var server = new OpenAssessment.Server(runtime, element);
        var ui = new OpenAssessment.StudioUI(runtime, element, server);
        ui.load();
    });
}
