__MAP_MESSAGES = {
        "ENV_CREATE" : "Creating NOISR environment...",
        "ENV_OK"    : "The environment is set and ready to go! ",
        "ENV_EXIT"  : "Live long and prosper! ",
        "NO_BOARD" : "no board",

        "READ_START" : "🟢 Started reading...",
        "READ_STOP" : "🟥 Stopped reading",
        "DATA_SAVE" : "Saving the precious data...",
        "DATA_LOAD" : "Loading the precious data...",

        "CREATED_LOGGER" : "I've created myself",
        "EASTER_EGG_LUIS_MELO_GREETING" : "Viva!",

        "PLOT_ERR_AUTOSCALE" : "No data in queue, so I've auto-scaled to standard",

        "STATUSBAR_READ_START" : "Reading!",
        "STATUSBAR_SCALE_CHANGED" : "Y-axis scale changed to:",
        "STATUSBAR_PIN_CHANGED" : "Connected to pin ",

        "TIMER_START" : "The timmer started counting!",

        "SIGNAL_STABILIZED" : "Signal stabilized",
        "SIGNAL_NOT_STABILIZED" : "Signal not stabilized",

        "CON_NEW"   : "Establishing a new connection... ",
        "CON_CHECKING_PORTS" : "Checking for Arduino connected ports... ",
        "CON_SERIAL_OK" : "Serial connection established! ",
        "CON_ARDUINO_SAYS" : "Handhake at Serial Monitor: Arduino says ",
        "CON_SERIAL_ERR" : "Serial not connected ",

        "CON_PORTS" : "Checking connected boards through USB ports...",
        "CON_CLICK_AGAIN" : "The Arduino seems to be busy... try again in 2 seconds!",
        "CON_ERR_PORTS" : "No Arduino found at this port",
        "CON_OK_PORTS" : "Arduino found on port(s)",
        "CON_SOL_PORTS" : "Check if the Arduino is connected... or alive",
        "CON_SOL_SERIAL" : "Is the Serial being used somewhere else?",
        "CON_ERR_TIMEOUT" : "Seems like the Arduino may be busy processing other threads :(",

        "ERR_THREAD_RUNNING" : "💥 Stop reading first! You wouldn't want to EXPLODE your expensive Raspberry PI"
    }

def _(msgid):
    """
        Returns a message from the messages map
    """
    return __MAP_MESSAGES.get(msgid, msgid)

def egg(lottery):
    eggs = [
        "'HTTP 418: I'm a teapot 🫖'",                     # HTTP: 418
        "'I'm sorry, Dave, I'm afraid I can't do that'",   # 2001 Space Odissey
        "'DON'T PANIC'",                                   # Hitchhikers Guide to the Galaxy
        "'Hello, World!'",                                 # Hello world
        "'Houston, we have a problem'"                     # Apollo 13
    ]
    return eggs[lottery % len(eggs)]