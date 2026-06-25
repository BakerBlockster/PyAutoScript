from PIL import Image, ImageTk, ImageDraw, ImageFont
import PIL
import base64
from io import BytesIO
import pyautogui as pag
import pydirectinput as pdi
from pynput import mouse, keyboard
from threading import Thread
from idlelib.tooltip import Hovertip
from tkinter import *
import tkinter as tk
import time
import os

def ImageToBase64(imagePath, optimize=True, compressLevel=9):
    with PIL.Image.open(imagePath) as img:
        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=optimize, compress_level=compressLevel)
        compressedBytes = buffer.getvalue()
        base64Bytes = base64.b64encode(compressedBytes)
        base64String = base64Bytes.decode('utf-8')
        
        return base64String

def Base64ToImage(base64String):
    if "," in base64String:
        base64String = base64String.split(",")[-1]
    imageBytes = base64.b64decode(base64String)
    buffer = BytesIO(imageBytes)
    
    return PIL.Image.open(buffer)

def StartThread(func, args):
    thread = Thread(target=func, args=args)
    thread.daemon = True
    thread.start()
    return thread

def on_press(key):
    global stopMacro
    if(key == keyboard.Key.esc):
        stopMacro = True
        return False

def on_release(key):
    pass
##    try:
##        print(f'Alphanumeric key released: {key.char}')
##    except AttributeError:
##        print(f'Special key pressed: {key}')

def on_move(x, y, injected):
    global newMacros
    if(not injected):
        newMacros[time.time()-startMacroTime] = ("mouse_move", (x, y))

def on_click(x, y, button, pressed, injected):
    global newMacros
        
    if(not injected and pressed):
        newMacros[time.time()-startMacroTime] = ("mouse_click", (x, y), str(button)[7:])
    elif(not injected and not pressed):
        newMacros[time.time()-startMacroTime] = ("mouse_release", (x, y), str(button)[7:])

def on_scroll(x, y, dx, dy, injected): pass

def WriteSavedMacros(data):
    file = open("PyAutoScript_Data ;)/macros.pyas", "w")
    file.write(str(data))
    file.close()

def GetSavedMacros():
    if(not os.path.exists("PyAutoScript_Data ;)/macros.pyas")):
        file = open("PyAutoScript_Data ;)/macros.pyas", "w")
        file.write("{}")
        file.close()
    return eval(open("PyAutoScript_Data ;)/macros.pyas", "r").read())

def RecordMacro(name, delay=0, autoSave=True):
    global newMacros, startMacroTime, stopMacro, recordingMacro, finishedRecording

    finishedRecording = False

    time.sleep(delay)

    newMacros = {}
    startMacroTime = time.time()
    stopMacro = False
    recordingMacro = True
    
    listenerM = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll)
    listenerM.start()

##    listenerK = keyboard.Listener(
##        on_press=on_press,
##        on_release=on_release)
##    listenerK.start()

    print(f"stopMacro: {stopMacro}")
    print(f"recordingMacro: {recordingMacro}")
    while not stopMacro and recordingMacro: pass
    
    listenerM.stop()
##    listenerK.stop()

    macros[name] = newMacros
    newMacros = {}
    if(autoSave): SaveMacro(name)
    print("recording done")

    recordingMacro = False
    finishedRecording = True
    ChangeButtonImage(recordButton, recordImage)
    playButton.config(state="normal")

def PlayMacro(name=None, delay=0):
    global stopPlayback
    global playingMacro

    stopPlayback = False

##    def on_press_loop(key):
##        global stopPlayback
##        if(key == keyboard.Key.esc):
##            stopPlayback = True
##            return False
##        
##    listener = keyboard.Listener(
##        on_press=on_press_loop)
##    listener.start()
    
    time.sleep(delay)

    print(selectedMacro)
    if(not name == None): macro = macros[name]
    elif(not selectedMacro == None): macro = macros[selectedMacro]
    else: return False
    
    startTime = time.time()
    inputsDone = 0
    macroKeys = list(macro.keys())
    print("playing macro")
    try:
        while inputsDone < len(macro) and not stopPlayback:
            if(time.time()-startTime >= macroKeys[inputsDone]):
                inpt = macro[macroKeys[inputsDone]]
                if(inpt[0] == "mouse_move"):
                    pdi.moveTo(inpt[1][0], inpt[1][1])
                elif(inpt[0] == "mouse_click"):
                    if(len(inpt) == 2): pdi.click(inpt[1][0], inpt[1][1])
                    else: pdi.click(inpt[1][0], inpt[1][1], button=inpt[2])
                elif(inpt[0] == "mouse_press"):
                    pdi.mouseDown(button=inpt[2])
                elif(inpt[0] == "mouse_release"):
                    pdi.mouseUp(button=inpt[2])
                inputsDone += 1
    except pdi.FailSafeException:
        errorWindow = Toplevel(root)
        errorWindow.title("Quit Macro")
        errorWindow.resizable(False, False)
        Label(errorWindow,text="This macro was closed because the mouse\nwas moved to the corner of the screen.\n\nThis is a safety feature and it can be disabled by checking\nthe 'Disable Screen Corner Fail-Safe' in the settings").grid(row=0,column=0,padx=10,pady=10)
        Button(errorWindow,text="Ok",command=errorWindow.destroy).grid(row=1,column=0,padx=10,pady=10)
    
    playingMacro = False
    ChangeButtonImage(playButton, playImage)
    recordButton.config(state="normal")

def SaveMacro(name=None):
    if(name == None):
        WriteSavedMacros(macros)
    else:
        currentMacros = GetSavedMacros()
        currentMacros[name] = macros[name]
        
        WriteSavedMacros(currentMacros)

def MacroKeys():
    return list(macros.keys())

def LoadMacro(name=None, override=False):
    global macros
    currentMacros = GetSavedMacros()
    if(name == None):
        for macro in currentMacros:
            if(macro not in macros or override):
                macros[macro] = currentMacros[macro]
    else:
        if(name not in macros or override):
            macros[name] = currentMacros[name]

def DeleteMacro(name=None, confirmation=False):
    global macros
    if(name == None and confirmation):
        macros = {}
    elif(name == None):
        print("Did not reset macros as confirmation was false")
    else:
        del macros[name]

def DeleteSavedMacro(name=None, confirmation=False):
    if(name == None and confirmation):
        WriteSavedMacros("{}")
    elif(name == None):
        print("Did not reset saved macros as confirmation was false")
    else:
        currentMacros = GetSavedMacros()
        del currentMacros[name]
        WriteSavedMacros(currentMacros)

def CompletelyDeleteMacro(name=None, confirmation=False):
    # Delete from chache
    global macros
    if(name == None and confirmation):
        macros = {}
    elif(name == None):
        print("Did not reset macros as confirmation was false")
    elif(name in macros):
        del macros[name]

    # Delete from file
    if(name == None and confirmation):
        WriteSavedMacros("{}")
    elif(name == None):
        print("Did not reset saved macros as confirmation was false")
    else:
        currentMacros = GetSavedMacros()
        del currentMacros[name]
        WriteSavedMacros(currentMacros)

    # Unselect if it was previously selected
    if(not selectedMacro == None and selectedMacro == name):
        UnselectMacro()

def LoopMacro(name, loops=None, delay=0):
    global stopPlayback

    stopPlayback = False
    
    if(loops == None):
        while not stopPlayback:
            PlayMacro(name, delay)
    else:
        for i in range(loops):
            PlayMacro(name, delay)
            if(stopPlayback): break
##    print("Loop ended")

def SelectMacro(name):
    global selectedMacro
    
    LoadMacro(name)
    selectedMacro = name
    macroLabel.config(text=name)

def UnselectMacro():
    global selectedMacro
    
    selectedMacro = None
    macroLabel.config(text="[No Macro Currently Open]")

def ChangeButtonImage(button, image):
    button.config(image=image)

def Open():
    global selectedMacro
    
    openMenu.delete(0, "end")
    currentMacros = list(GetSavedMacros().keys())
    for macro in currentMacros:
        openMenu.add_command(label=macro,command=lambda macro=macro: SelectMacro(macro))

def Delete():
    global selectedMacro
    
    deleteMenu.delete(0, "end")
    currentMacros = list(GetSavedMacros().keys())
    for macro in currentMacros:
        deleteMenu.add_command(label=macro,command=lambda macro=macro: CompletelyDeleteMacro(macro))

def Record():
    global recordingMacro, finishedRecording
    
    if(not recordingMacro):
        finishedRecording = False
        UnselectMacro()
        macroLabel.config(text="[Recording]")
        StartThread(lambda: RecordMacro("New Recording", autoSave=False), ())
        recordButton.config(image=stopRecordImage)
        playButton.config(state="disabled")
        recordingMacro = True
    else:
        recordingMacro = False
        macroLabel.config(text="[Saving]")
        
        while not finishedRecording: pass
        
        SelectMacro("New Recording")
        playButton.config(state="normal")

def Play():
    global playingMacro
    global stopPlayback
    
    if(not playingMacro):
        playingMacro = True
        StartThread(PlayMacro, ())
        playButton.config(image=stopImage)
        recordButton.config(state="disabled")
    else:
        playingMacro = False
        stopPlayback = True
        playButton.config(image=playImage)
        recordButton.config(state="active")

def Save():
    def SaveButton(name, window):
        macros[name] = macros["New Recording"]
        del macros["New Recording"]
        
        SaveMacro(name)
        SelectMacro(name)
        Open()
        window.destroy()
        
    save = Toplevel(root)
    save.title("Save")
    save.resizable(False, False)

    Label(save,text="Macro Name").grid(row=0,column=0)
    text = tk.StringVar()
    Entry(save, textvariable=text).grid(row=1,column=0)
    Button(save,text="Save",command=lambda: SaveButton(text.get(), save)).grid(row=2,column=0)

def ChangeKeybind(ID, binding=False):
    global waitingForInput
    
    def key_press(key):
        global keybinds, waitingForInput
        strKey = str(key).replace("'", "").replace("Key.", "").replace("<", "").replace(">", "")
        keybindButtons[ID].config(text=strKey)
        keybinds[ID] = strKey
        UpdateKeybinds()
        waitingForInput = False
        return False

    if(binding == False):
        keybindButtons[ID].config(text="[Press a Key]")

        chosenKey = None
        listenerK = keyboard.Listener(
            on_press=key_press)
        listenerK.start()
        waitingForInput = True
    else:
        keybindButtons[ID].config(text=str(binding))
        keybinds[ID] = binding
        UpdateKeybinds()

def Keybinds():
    keybindsWindow = Toplevel(root)
    keybindsWindow.title("Keybinds")
    keybindsWindow.resizable(False, False)

    Label(keybindsWindow,text="Keybinds").grid(row=0,column=0,columnspan=3,padx=150,pady=10)

    Label(keybindsWindow,text="Play Macro").grid(row=1,column=0,padx=10,pady=3)
    playKeyButton = Button(keybindsWindow, text=str(keybinds["play"]),command=lambda: ChangeKeybind("play"))
    playKeyButton.grid(row=1,column=1,padx=10,pady=3)
    keybindButtons["play"] = playKeyButton
    Button(keybindsWindow,text="Reset",command=lambda: ChangeKeybind("play", binding=None)).grid(row=1,column=2,padx=10,pady=3)

    Label(keybindsWindow,text="Stop Playback").grid(row=2,column=0,padx=10,pady=3)
    stopPlayKeyButton = Button(keybindsWindow, text=str(keybinds["stop play"]),command=lambda: ChangeKeybind("stop play"))
    stopPlayKeyButton.grid(row=2,column=1,padx=10,pady=3)
    keybindButtons["stop play"] = stopPlayKeyButton
    Button(keybindsWindow,text="Reset",command=lambda: ChangeKeybind("stop play", binding=None)).grid(row=2,column=2,padx=10,pady=3)

    Label(keybindsWindow,text="Record Macro").grid(row=3,column=0,padx=10,pady=3)
    recordKeyButton = Button(keybindsWindow, text=str(keybinds["record"]),command=lambda: ChangeKeybind("record"))
    recordKeyButton.grid(row=3,column=1,padx=10,pady=3)
    keybindButtons["record"] = recordKeyButton
    Button(keybindsWindow,text="Reset",command=lambda: ChangeKeybind("record", binding=None)).grid(row=3,column=2,padx=10,pady=3)

    Label(keybindsWindow,text="Stop Recording").grid(row=4,column=0,padx=10,pady=3)
    stopRecordKeyButton = Button(keybindsWindow, text=str(keybinds["stop record"]),command=lambda: ChangeKeybind("stop record"))
    stopRecordKeyButton.grid(row=4,column=1,padx=10,pady=3) 
    keybindButtons["stop record"] = stopRecordKeyButton
    Button(keybindsWindow,text="Reset",command=lambda: ChangeKeybind("stop record", binding=None)).grid(row=4,column=2,padx=10,pady=3)

def Settings():
    def validateNumbers(newValue):
        if(newValue == "" or newValue.isdigit()):
            return True
        return False
    
    settingsWindow = Toplevel(root)
    settingsWindow.title("Settings")
    settingsWindow.resizable(False, False)

    Label(settingsWindow,text="Settings").grid(row=0,column=0,columnspan=2,padx=10,pady=10)

    # Macro Pause
    macroPauseLabel = Label(settingsWindow,text="Pause time between actions (milliseconds)")
    macroPauseLabel.grid(row=1,column=0,padx=10,pady=3)
    Hovertip(macroPauseLabel,"This determines how long the macro\nshould wait between inputs.\nIf the pauses are too long,\nthe macro will effectivly run in\nslow motion until it catches up.")
    macroPauseSpinbox = Spinbox(settingsWindow,from_=0,to=1000,textvariable=settings["macroPause"],validate="key",validatecommand=(settingsWindow.register(validateNumbers), '%P'),command=lambda: UpdateSetting("macroPause"))
    macroPauseSpinbox.bind("<Return>", lambda _: UpdateSetting("macroPause"))
    macroPauseSpinbox.grid(row=1,column=1,padx=10,pady=3)

    # Disable Screen Corner Fail-Safe
    cornerFailSafeLabel = Label(settingsWindow,text="Disable Screen Corner Fail-Safe")
    cornerFailSafeLabel.grid(row=2,column=0,padx=10,pady=3)
    Hovertip(cornerFailSafeLabel,"As long as this is not disabled, if the\nmouse moves to a corner of the screen\nthe macro will immidiatly end.\nThis is a safety feature and is recommened\nto keep enabled if you don't have\na keybind to stop the macro.")
    Checkbutton(settingsWindow,variable=settings["cornerFailSafe"],command=lambda: UpdateSetting("cornerFailSafe")).grid(row=2,column=1,padx=10,pady=3)

##    # Min Hold Time
##    Label(settingsWindow,text="How long till a click becomes a hold (milliseconds)").grid(row=3,column=0,padx=10,pady=3)
##    macroPauseSpinbox = Spinbox(settingsWindow,from_=0,to=1000,textvariable=settings["minHoldTime"],validate="key",validatecommand=(settingsWindow.register(validateNumbers), '%P'),command=lambda: UpdateSetting("minHoldTime"))
##    macroPauseSpinbox.bind("<Return>", lambda _: UpdateSetting("minHoldTime"))
##    macroPauseSpinbox.grid(row=3,column=1,padx=10,pady=3)


def UpdateKeybinds():
    keybindsStr = "{\n"
    keybindsStr += f"'play': '{keybinds['play']}',\n"
    keybindsStr += f"'stop play': '{keybinds['stop play']}',\n"
    keybindsStr += f"'record': '{keybinds['record']}',\n"
    keybindsStr += f"'stop record': '{keybinds['stop record']}',\n"
    keybindsStr += "}"
    keybindsStr = keybindsStr.replace("'None'", "None")
    file = open("PyAutoScript_Data ;)/keybinds.conf", "w")
    file.write(keybindsStr)
    file.close()

def LoadKeybinds(ID=None):
    global keybinds

    for i in range(2):
        try:
            loadedKeybinds = eval(open("PyAutoScript_Data ;)/keybinds.conf", "r").read())
            # Play
            if(ID == "play" or ID == None):
                if("play" in loadedKeybinds):
                    keybinds["play"] = f"{loadedKeybinds['play']}"
                else: keybinds["play"] = None
            # Stop Play
            if(ID == "stop play" or ID == None):
                if("stop play" in loadedKeybinds): keybinds["stop play"] = f"{loadedKeybinds['stop play']}"
                else: keybinds["stop play"] = None
            
            # Record
            if(ID == "record" or ID == None):
                if("record" in loadedKeybinds): keybinds["record"] = f"{loadedKeybinds['record']}"
                else: keybinds["record"] = None
            # Stop Record
            if(ID == "stop record" or ID == None):
                if("stop record" in loadedKeybinds): keybinds["stop record"] = f"{loadedKeybinds['stop record']}"
                else: keybinds["stop record"] = None
            break
        except:
            print("except")
            file = open("PyAutoScript_Data ;)/keybinds.conf", "w")
            file.write("{}")
            file.close()

def UpdateSetting(ID=None):
    global settings

    # Check each settings to be updated and update settings dict for each
    if(ID == "macroPause" or ID == None):
        pdi.PAUSE = int(settings["macroPause"].get())/1000 if int(settings["macroPause"].get()) > 0 else False
        print(f"Macro Pause is now {int(settings['macroPause'].get())}")
    if(ID == "cornerFailSafe" or ID == None):
        pdi.FAILSAFE = not bool(settings["cornerFailSafe"].get())
        print(f"Corner Fail Safe is now {not bool(settings['cornerFailSafe'].get())}")
    if(ID == "minHoldTime" or ID == None):
        print(f"The minimum hold time is now {int(settings['minHoldTime'].get())}")

    settingsStr = "{\n"
    settingsStr += f"'macroPause': tk.IntVar(value={settings['macroPause'].get()}),\n"
    settingsStr += f"'cornerFailSafe': tk.IntVar(value={settings['cornerFailSafe'].get()}),\n"
    settingsStr += f"'minHoldTime': tk.IntVar(value={settings['minHoldTime'].get()}),\n"
    settingsStr += "}"
    file = open("PyAutoScript_Data ;)/settings.conf", "w")
    file.write(settingsStr)
    file.close()

def LoadSettings(ID=None):
    global settings

    for i in range(2):
        try:
            loadedSettings = eval(open("PyAutoScript_Data ;)/settings.conf", "r").read())
            # Change the delay between macro actions
            if(ID == "macroPause" or ID == None):
                if("macroPause" in loadedSettings): settings["macroPause"] = loadedSettings["macroPause"]
                else: settings["macroPause"] = tk.IntVar(value=10)
            
            # Disable the Corner Fail Safe
            if(ID == "cornerFailSafe" or ID == None):
                if("cornerFailSafe" in loadedSettings): settings["cornerFailSafe"] = loadedSettings["cornerFailSafe"]
                else: settings["cornerFailSafe"] = tk.IntVar(value=0)
            
            # Min hold time
            if(ID == "minHoldTime" or ID == None):
                if("minHoldTime" in loadedSettings): settings["minHoldTime"] = loadedSettings["minHoldTime"]
                else: settings["minHoldTime"] = tk.IntVar(value=100)
            break
        except:
            file = open("PyAutoScript_Data ;)/settings.conf", "w")
            file.write("{}")
            file.close()

def CloseWindow():
    global keybindListener
    keybindListener.stop()
    root.destroy()

# Variable Setup
macros = {}
selectedMacro = None
newMacros = {}
startMacroTime = 0
stopMacro = False
stopPlayback = False
playingMacro = False
recordingMacro = False
finishedRecording = False
waitingForInput = False

# Tkinter Setup
root = Tk()
root.title("PyAutoScript")
root.resizable(False, False)

# Top Menu
menu = Menu(root)
root.config(menu=menu)
root.protocol("WM_DELETE_WINDOW", CloseWindow)

fileMenu = Menu(root)
menu.add_cascade(label="File", menu=fileMenu)
openMenu = Menu(fileMenu, postcommand=Open)
fileMenu.add_cascade(label="Open", menu=openMenu)
fileMenu.add_command(label="Save", command=Save)
deleteMenu = Menu(fileMenu, postcommand=Delete)
fileMenu.add_cascade(label="Delete", menu=deleteMenu)

menu.add_command(label="Keybinds", command=Keybinds)

menu.add_command(label="Settings", command=Settings)

# Main UI
macroLabel = Label(root, text="[No Macro Currently Open]")
macroLabel.grid(row=0,column=0,padx=40,pady=40,columnspan=2)

playImage = ImageTk.PhotoImage(Base64ToImage('iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAACPUlEQVR42u3bsS4EcRSF8W+HKEWhERINjXqegngFkYho8UL7DkJ4iCnpCUrF1iI0JNtg1w7Ovfecbovdnfy//LI7xYDneV6hdZzRseKD6GdND5+xC9zQsefjnH2DHoS8jr26AI5oefTR/p+Q8e0A13Ts+2g1hGAtWkKsRViItYgJsRZhIdYiJsRahIVYi5gQaxEWYi1/KmQdmLMWnSDLwBawOPE7loAhHed0rDrIb2wB2LAWrR/1gbVo/suyFsG/vdYieh9iLYI3htYid6duLZJBrEUwiLWIBimupZG+uoJaGvkrLKalCXOlRbQ0oTwX0BIrSAEtMYMk1hI3SFIt8YMk05IjSCItuYIk0JIvSHAteYME1ZI7SEAtNYIE0lInSBAt9YKIa6kZRFhL7SCCWhxETIuDiGlxEDEtDvKdlk2mec7sQ8vxT7923if/xZ6Ae5jiob0RcELL0EH63DNw9368k+8KOKTlYZavdpDPVLxMpeIUGNLO/gCsgwiocBAxFQ4ipsJBxFTUDiKoom4QURX1goirqBUkgIoaQQKpyB8kmIq8QYKqyBkksIpcQRKoyBMkiYr4QZKpiB0koYqYQRKriBckuYo4QYqoiBGkkArtIAVV6AYpqkIvSHEVWkGsQiSIVQgFsQqRIFYhFMQqRIJYhVAQqxALcmsV007hkbYRcABsV4+hcGNoFSJCrEJIiFWICLEKISFWISLEKoSEWIWIEKsQEmIVIkKsQmYdl3Ss+SB0ggx8CJ7neSX3Bu7iZEQkengfAAAAAElFTkSuQmCC'))
stopImage = ImageTk.PhotoImage(Base64ToImage('iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAD20lEQVR42u2dzUtUURiHH60cNTOzmo1mkO2KwLj7COo/iFoUQbUqKiOD+RsuJlpQtCqoNn3+Ay3E/UAf0E6jwhapgx+NM+OY2uLcIIJ7r3pnjjP3/p7tuc7Me57znnPPEd4DQgghhBBCCCGEEELUBw3V/oJshlbgNHAC6AN6gTSQqvG+KQHTwATwHhgD3jkuhboUks1wDOgHzgJtMRnAi8BLYMRx+VQXQrIZuoFB4JyNDNwi1jwxdxyXyZoVks1wHngItCdkyl8Arjsuz2pKSDbDNmDIm6KSyD1gwHFZ2XIhnozHwMWEvyA9BS5HldJYgR8yJBng9cHQlmaIt2Y8X8+z7c3Q0Qo7U5DaDtsaa7t3V1Zh6TcsLsFcARZK6xcTZU1piCCjG/gctoDvboGuDmhpqu/hXyzDjzmYL4Y++gs46rh8tz1lDQbJaAB6OuFwuv5lgInhcBoOdoaO4l3AXasZ4m36Pvj9fQPQmzbZEct33SKMT5nNSMA+5bjj8sFWhvQHyTzQGV8ZAO0t0LM3dKDfspIh3tnUT7/jkN0tJrWTwPhU4JpSANKOy2K1M+Q0AWdTXR3Jec/t3hPY3AqcsjFlnQh6tY3DAr5emneYmAM4aUNIn19DR2vydoMhMR+3IaTXr2FnKnlC2oJjPmRDyH6/htT25AlpCo55nw0hvrNmrR+HVIOQmFM2hIgqIiESIiREQoSESIiQEAkREiIhQkKEhEiIkBAJERIiIUJCJERIiJAQCRESIiFCQiRESIiECAkREiIhQkIkREiIhAgJkRAhIaISQpb8GlZWk9eBITGXbQiZ9jX1O3lCysExz9gQMuHXsLiUPCEhMX+xIeS9X8NcIXlCZgub66tKChnza1goQWk5OTJKy6HlY0dtCHkH/mXrJmeTI+RHcKwFr6+qK8SrIfjKr32+CDP5+MvI5WEuuIbvG8clbyNDAEYIqJL6PWdKqcaVhSJ8ywU+sgYMW9sYOi4fg7JkDVOxM46ZksuH1uwFeOu4G1/Qo+7UBzBltX2lfMuZHx+Hhb60DBNT8DUXKiMP3N7s90Qtxn8Jc1VFKO3NsMcrxt9UJ8X4y14x/tmNFeO/4rjr65OKC/GkPACuIQAeOS5Xo3xAJcbpTeCFXPACuBH1QyIL8W6U+Xv3VGIzA7jguEQ+zav0pWCXgPvE55q8MPJAf5Q1oxpT1r/Z8gQ4Arwm9GWkrlkD3gBHKimj4hnyX7b0Ya5sOIMpTB8HCp6I4c3uM7ZMyD9i2jA3KpzE1I0/hKn4XOtl+8uY/2d8wZzajmKuXk3AwZAQQgghhBBCCCGEEOH8AaND6FE/06twAAAAAElFTkSuQmCC'))
recordImage = ImageTk.PhotoImage(Base64ToImage('iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAGm0lEQVR42u2dz28WRRjHP2/5UVKKaQtIC4qABIIQL90EDFFOcvRAQiIH4I5NUInp32AICgnlLj1IQuLBY71AjPxIXjwYkECV4g+gUGmppYVS6OthntI32J2Z3Xd2u+/ufJM3kMy+3Znn8z4788zOPANeXl5eXl5eXl5eXl5ehVapnipbhgXAGmAD0A6sAJqBRXLJFDAGPAQGgVvAnQBeeCBuALwJ7AJ2Ap3AVqAp4p+ZAK4BV4ALwLkA/vJA7CFsBPYDe4BtCd3mKvAd0BvAbx7I/yE0AQfk817Kt78InAZOB8qbigukDK8BXcCnwMp5tsUQcBzoCWC0UEDK0AgcAb4AWjL21BwFjgFHA3iaeyBl+BA4CWzK+ICnH+gKoC+XQMrQCpwCPq61wo3yWQg0oMbCoMa208BzYFI+ldqrfgY4FMBIboCUYTvwLbA+6ncXS6CxTP5tjFDpikB5LMHJY+BZvCYMAPsCuFz3QMrwGfBlVfBm1EKgTT5LHddnQqLGYfGkCJoCugP4ui6BSFR9AvjE9jtLJPxulUdRkqoIlEEi99w9wOGkov9SQjAagV5gry2I1TLcSnuUUQEeAXejgTkL7A/UEzHbQATG98Bu07UNQAfwegoeYdI08AC4J/+3UB/wkWsoJccwFkjnbfSMpdLDN2ZsrDspPfi4vafsc/n4cv3DPGEDYxWwOYMwkDptljpaaK+0OXseIqOpr0w3Wyejp3rQMHDbLpb53NXoq+QIxnbgR93QtgF4GzV5VU/6F/jd3K9MAe+7iFNKDmC0ot41rNfB2JRATJGWxoGbZigDQGetEb2LPuSUDkZJPKNeYcwMQDaaf73rxRbz5yEyUdhnqmUb+dAI6p2wQbsD+CF1IBJv/IJm1nYV8Ab50t/Aff0lN4F348YntTyyjuhgLEWtRsib1pgfv5vENul5iLzp+4OQl0sNwDsZjTNcBY+/6jv5R8BbgRqkpeIhXWje9HXkGMZM8Nihv6RFbJS8h8iChNuEvANfAmxh/uemktY0cB3thOQQsC7qwok4djuAZkHC6gLAmDHcav0lK8VWpAGEMO9ooThqkTZrdDBRILKILXTdVDt1tjbVQRBn6Et2lNVcZWIesj+sYCFqDqVoapW2x7GZCyB7wgraCtJ3zOUlbTFtVhMQWfi8TQekqFquL95ShrVJeMiusILF1PfkYa1qEhto9EESQHaGFTTj1RzTdrUA6QwrWOZ5mGzQ6RSILF7Y6j0ktodsLc+ueHXiIWsI2bk0s9a26DIscW3CcvLbFsiGmBUp1PC3MaYN4wBp1wHxsrJFu0sgK3QRupeVLZa7BNLsKtTPsxpqGohFs2foeqsFnoOtLRa5BOKVDS97qamwghfehra2mHIJ5HFYwbTnYGuLMZdA/gkreO452NrioUsgg2EFk56DrS0GXQK5patExbN4ueM3jg3jALlDyHKWivcSmx/mhNjQDRDZsnUtco9fIBlscM1221uUOOTnmoYPOZfBBldcxyEAP3kPie0hF5IAci6s4BkZSDQ1j5rAmLLjvHMgkhbvak2D7JzK0PbrAfyZhIeASos3p4YLOvydSdERx2YugPTqotThAgIZMUfovYkBkYSRF3WhaKVg3mEIvy8FcCNJDwGVMHJOPUVtHSqKHgFP9Jd8E/VvxgUyFFZ4l2LMAE9LWzUa0v14nQGRHUHHdV7yoABAHmBM53Q8TtrZuG8Me9CkUr1Hvue3JqWNGo2KjUgFSDCbSjXUnQdy2sFXpG2Gx/KxuLl/a3mnfhSVSnVOjWM5vVlnuoMxl1a/2IZUgUiSYe3W3/s5i01GMGZxAJXr92nqQARKHyqvbahuE2P3fAY1Jo8qg87UmnjZxTKgQ7q6VlD5psbrGMY4KiI29IkDYgvmFYjkh9qHZpnLNCojy1ideoZFrqwpVO7FkXkHIlAuA92mQKqflPJ1O+wz+u0C3W5XWa9dZyU9iUXi5FWozRJZ3cZQkdHUfbvLe4KYeU0S85AqHUalTsU0+rqR0eBxUupmCeOstNmZfCLlqkdq7hIpvwLFpxrPChCBEisZfwcqXUUpBRAjqPcZT6J9tf6S8b8CJvZxFcuJfkaeSYU9ruIVKP5AlywBESj+yKMsAakC4w8FyxKQqlGYPzYvK0CqwPiDJbMEpArMzNGrB4EdKd/+Emp1iD96NQTOZmYPJ96S0G2uM3s48Y0stT/rx3evRSX/cnl89/koa209EHP0n+sD7r28vLy8vLy8vLy8vLwKrv8AGOGlkuSgcsQAAAAASUVORK5CYII='))
stopRecordImage = ImageTk.PhotoImage(Base64ToImage('iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAD9klEQVR42u2dTW8TVxSGHxNhY+wkVCoGREKlJDuqSolmH0Uq/6CCBQhp6KpV21Sl/yKNklYCdYWltpsUwh/IImJvKYDELkF8GEFDEY5jJ3Ha1F3MFEWV5k7I2Nf2zPtsjzOTuc+c+zXSuSCEEEIIIYQQQgghRG+QavcNipSOAxeASWAcGAUKQKbL22YHeA2sASvAPWDJxdnqSSFFSp8A08BFIB+TF7gO/A7MuzgPe0JIkdIQMANcspGBHaLpi/nexSl3rZAipcvATWAgIV1+FfjKxfm1q4QUKfUBs34XlUR+BK67OHsdF+LLuAVcTfgE6RfgWlQpR1rwj8xKBvhtMNvRDPHHjN8O8tscA/Rzgiw5jpKhj76ubt099viLBtvU2aRCneqBxUQZU1IRZAwBj8IG8DyDFDhLhmxPv/4NtlnnBTU2wn66CXzs4jyz3WXNmGSkSHGacwwz1vMyADJkGWaMM3xEyvwe9wM/WM0Qf9F3P+jvU6QYYpQ8g7EcLGpUKbNKk6ZpnTLh4ty3lSHTJpmnGI6tDK8bHuA058Je9G+tZIi/N/VH0HZInkGGGUvEtOo5q6YxZQsouDj1dmfIBQx7UwXOJmaeW2DIFD4OfGqjy5o0TW3jMIAffKA/Rs48yZyyIWQ8eHpxInGrwZBnnrAhZDQokCWXOCFZ85eFERtCTgYFjnb9N6fWkyZtCn9oQ8ixoEC3b4e0gyPmZ87YECLaKlhIiJAQCRESIiFCQiRESIiECAkREiIhQkIkREiIhAgJkRAhIUJCJERIiIQICZEQISESIiRESIiECAmRECEhEiIkREKEhIjoQhpBgX/YS1wDhjzzrg0hr4Pv3kickF1zm/9pQ8haUGCbeuKEhDzzYxtCVoICm1QSJ2STt4dqq1YKuRcUqFOlwU6CuqudsPKxyzaELEFwnq5TToyQdV6Ywlt+W7VXiF9D8HZQvMYGlfcfy3qOCm/CuuhFF6dmax0yD8E1Ul/xjNrBK0H3HDWqvOKp6SdNYM7awtDFeWDKkiZNyqzGMlMqvAmr2Qtw18VZsSbE5zpeWe1AKS95ynNWYzHQ77JDmTVe8iRMRg347rD3iVqM38U7qiIUrxj/B2TJkSYdVomtK1bgu+/mUW/fpxj/5y7OrY4I8aXcAL5EAPzs4nwR5QKt2Fz8BliQCxaAr6NeJLIQ/0SZ/86eSmxmAFdcnL+jXqjVh4K5wE/E55i88BkwTEcZM9rRZe3PliJwHrhjWqfEgCawCJxvpYyWZ8j/smUc78iGz/AK08eBLV/E3GHXGR0Tsk9MHu9EhSm8uvEjeBWf012/9PC+ZzzG27Vdxjt6tYYQQgghhBBCCCGEEIJ/AY6p6+4e5s5VAAAAAElFTkSuQmCC'))

playButton = Button(text="Play",image=playImage,command=Play)
playButton.grid(row=1,column=0,padx=40,pady=40)
recordButton = Button(text="Record",image=recordImage,command=Record)
recordButton.grid(row=1,column=1,padx=40,pady=40)

os.makedirs("PyAutoScript_Data ;)", exist_ok=True)

# Keybinds Variable
keybinds = {}
keybindButtons = {}

LoadKeybinds()
UpdateKeybinds()

# Settings Variables
settings = {}

LoadSettings()
UpdateSetting()

# Keybind Check
def key_press(key):
    global keybinds, stopPlayback, stopMacro, waitingForInput
    
    key = str(key).replace("'", "").replace("Key.", "").replace("<", "").replace(">", "")
    if(key in list(keybinds.values())):
        foundKey = False
        for keybind in keybinds:
            if(foundKey or waitingForInput): break
            else: foundKey = True
            if(key == keybinds[keybind]):
                if(keybind == "play" and not playingMacro and not recordingMacro): Play()
                elif(keybind == "stop play" and playingMacro and not recordingMacro): Play()
                elif(keybind == "record" and not recordingMacro and not playingMacro): Record()
                elif(keybind == "stop record" and recordingMacro and not playingMacro): Record()
                else: foundKey = False
            else: foundKey = False

keybindListener = keyboard.Listener(
    on_press=key_press)
keybindListener.start()

root.mainloop()
