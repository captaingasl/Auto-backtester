import os, sys, time, numpy, pandas, pynput, pyautogui, datetime, IPython

class AutoMQT:

    positions = dict(
        posGraphClose = "First, open any candle chart and maximize it.\n" \
            + "Then, point at the X button that would close the chart...",
        posSymbolPanel = "Close all of the opened candle charts before going on.\n" \
            + "Then, open the symbol watchlist, and point near the center of the panel...",
        posSymbolClear = "Please, make sure you NEVER close the symbol watchlist panel.\n" \
            + "Now, right-click around said panel center. Then, point at the \"Hide all\" option...",
        posSymbolFirst = "Now, please make sure that your watchlist only displays two symbols.\n" \
            + "Delete or hide all until 2 remain.\nThen, point at the one at the 2nd place/row...",
        posSymbolTester = "It's time to open the Strategy Tester panel in MetaTrader 4.\n" \
            + "Make sure that you enlarge it enough so that every clickable object is visible.\n" \
            + "Locate the symbol selector draglist (below the EA selector) and point at it...",
        posTesterRun = "Now, point at the [\"Start\"] button in charge of executing a new backtest...",
        posPropsOpen = "Now, point at the [\"Expert properties\"] button that opens the EA window...",
        posPropsClose = "Click on said [\"Expert properties\"] button and open the EA config window.\n" \
            + "Locate the [\"OK\"] button that confirms the parameter settings, and point at it...",
        posPropsFirst = "You must now locate the top most parameter row in the list.\n" \
            + "Doesn't really matter to which parameter is related to.\n" \
            + "Point at it below the leftmost \"Value\" column...",
        posPropsSecond = "Now do exactly the same but pointing at the second row in the list...",
        posResultOpen = "You can now close the EA config window with any button.\n" \
            + "You must now find the \"Result\" tab on the bottom of the Strategy Tester panel.\n" \
            + "Said tab is only visible after one backtest.\nSo if not visible, start a backtest " \
            + "and stop it right away.\nOnce you can locate the \"Result\" label, point at it...",
        posResultPanel = "Next, open the \"Result\" tab and point at the center of the panel...",
        posResultSave = "Now, right-click at said center of the panel to open the option list.\n"\
            + "Point at the \"Save as report\" option...",
        posSavePath = "Finally, point at any place along the path field...\n" \
            + "(that's where the actual folder name is written, next to the arrow icons)",
        posSaveFile = "Last but not least, point at the \"Save\" push button...")

    corrections = {"/": "-", ":": "."}    ;    columns = ["page", "cell", "type"]

    def __init__(self, waitTest: float = 2.5, waitSave: float = 0.5, waitInput: float = 0.5):
        
        self.xmax, self.ymax = pyautogui.size()
        self.active = self.paused = True  ;  cwd = os.getcwd()
        self.symbol = self.test = self.config = self.format = None
        self.waitTest, self.waitSave, self.waitInput = waitTest, waitSave, waitInput
        for attr in AutoMQT.positions.keys(): object.__setattr__(self, attr, None)
        sys.stdout.write("\nWelcome. Please, open your MetaTrader 4 platform.")
        sys.stdout.write("\nBe sure to follow the upcoming instructions carefully...")
        self.locateCSV() if ("pos.csv" in os.listdir(cwd)) else self.locate()
        self.path = cwd + "\\" + datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")
        sys.stdout.write("\nOpen MT4 and press SPACE to begin.") ; os.mkdir(self.path)
        with pynput.keyboard.Listener(on_press = self.listen) as listener:

            self.setup()
            while True:
                while self.paused: pass
                if not self.active: break
                if not self.symbols(): break
                self.setSymbol()
                while True:
                    while self.paused: pass
                    if not self.active: break
                    if not self.tests(): break
                    self.setTest()
                    while True:
                        time.sleep(2)
                        while self.paused: pass
                        if not self.active: break
                        if pyautogui.locateOnScreen("started.png"): break
                    print("\nBacktesting:", dict(symbol = self.symbol,
                        time = datetime.datetime.now().strftime("%H:%M"),
                        **self.test), "\n...you can modify files now.")
                    while True:
                        time.sleep(2)
                        while self.paused: pass
                        if not self.active: break
                        if pyautogui.locateOnScreen("finished.png"): break
                    while self.paused: pass
                    if not self.active: break
                    self.saveResult()
            
            listener.join()
                
    def listen(self, key: pynput.keyboard.Key):
        
        action = f"\n Key: <{key}>"
        if (key == pynput.keyboard.Key.esc):
            event = "ended: you can now close this window"
            print(action + " - Process %s." % event)
            self.paused = self.active = False ; return True
        if (key == pynput.keyboard.Key.space):
            event = "active" if self.paused else "paused"
            print(action + " - Process %s." % event)
            self.paused = not self.paused ; return True
        if (key == pynput.keyboard.Key.backspace):
            event = f"reset for {self.symbol}"
            with open("tests.csv", "rt") as CSV: tests = CSV.read()
            with open("temp.csv", "wt") as CSV: CSV.write(tests)
            print(action + " - Process %s." % event) ; return True

    def setup(self):

        width = len(self.columns)  ;  generator = None  ;  self.format = ""
        self.config = pandas.read_csv("config.csv", index_col = 0, header = None)
        if (self.config.shape[1] > width):
            generator = self.config.iloc[:, width :]
        self.config = self.config.iloc[:, : width]
        self.config.columns = self.columns
        self.config["type"] = self.config["type"].apply(func = eval)
        for key in self.config.index: self.format += f", {key} = %s"
        if isinstance(generator, type(None)): return
        generator = generator.to_dict().values()
        generator = map(pandas.Series, generator)
        self.generate(*generator)

    @staticmethod
    def generate(meshed: pandas.Series, scope: pandas.Series):

        scope = scope.apply(eval) ; index = scope.index
        tests = pandas.DataFrame(columns = scope.index)
        default = scope.apply(lambda array: array[0])
        for label, values in scope.to_dict().items():
            for value in values:
                test = default.copy()
                test.at[label] = value
                tests.at[len(tests)] = test
        mesh = numpy.meshgrid(*scope.loc[meshed])
        mesh = [axis.reshape(-1) for axis in mesh]
        size = len(mesh[0])
        mesh = zip(index, mesh)
        for n in range(size):
            test = default.copy()
            for label, axis in mesh:
                test.at[label] = axis[n]
            tests.at[len(tests)] = test
        tests.drop_duplicates(inplace = True)
        tests.reset_index(inplace = True, drop = True)
        tests.iloc[0:].to_csv("tests.csv", index = False, header = False)
    
    def symbols(self):

        try:
            with open("symbols.csv", "rt") as CSV:
                symbols = CSV.read().split("\n")
                self.symbol = symbols.pop(0)
                assert self.symbol.isalnum()
            with open("symbols.csv", "wt") as CSV:
                CSV.writelines("\n".join(symbols))
                OK = True
        except: OK = False
        with open("tests.csv", "rt") as CSV: tests = CSV.read()
        with open("temp.csv", "wt") as CSV: CSV.write(tests)
        print(f"Actual symbol: \"{self.symbol}\", pending: {symbols}")
        return OK

    def tests(self):

        try:
            with open("temp.csv", "rt") as CSV:
                tests = CSV.read().split("\n")
                self.test = tests.pop(0).split(",")
                types = zip(self.test, self.config["type"])
                self.test = [tp(value) for (value, tp) in types if value != ""]
                self.test = pandas.Series(self.test, index = self.config.index)
            with open("temp.csv", "wt") as CSV:
                CSV.writelines("\n".join(tests))
                OK = True
        except: OK = False
        return OK
    
    def locate(self):

        for step, (attr, description) in enumerate(AutoMQT.positions.items()):
            step = f"[{step + 1} / {len(AutoMQT.positions)}]"
            description = description.replace("...", " with your mouse pointer.")
            sys.stdout.write(f"\r => {step} {description}\nThen, press \"CTRL\".")
            def detect(key): return (key != pynput.keyboard.Key.ctrl_l)
            with pynput.keyboard.Listener(on_press = detect) as OK: OK.join()
            object.__setattr__(self, attr, pyautogui.position())
            sys.stdout.flush()
        pos = pandas.DataFrame(columns = ["x", "y"],
            index = AutoMQT.positions.keys())
        for attr in AutoMQT.positions.keys():
            value = self.__getattribute__(attr)
            pos.loc[attr, :] = [value.x, value.y]
        pos.to_csv("pos.csv", header = False)
        sys.stdout.write("\n\nGreat! We may now proceed with the backtesting process.")
        sys.stdout.write("\nPlease, make MetaTrader 4 maximized and visible at all times.")
        sys.stdout.write("\nWe STRONGLY suggest you to drag and place this window towards the trading chart area.")
        sys.stdout.write("\nIf you wish to pause/resume the process, hold/press \"CTRL + ALT + 0\" at any moment.")
        sys.stdout.write("\nTo definitively stop the process, just close this after pause or during one backtest.")
        time.sleep(3)
    
    def locateCSV(self):

        positions = pandas.read_csv("pos.csv",
            names = ["x", "y"], index_col = 0)  
        for attr in AutoMQT.positions.keys():
            x, y = positions.loc[attr, :].values
            error = lambda s: f"Invalid \"{s}\" for \"{attr}\"."
            assert (0 <= x <= self.xmax), error("x")
            assert (0 <= y <= self.ymax), error("y")
            pos = pyautogui.Point(x, y)
            object.__setattr__(self, attr, pos)

    def setSymbol(self):
        
        pyautogui.moveTo(self.posSymbolPanel)  ;  pyautogui.rightClick()
        pyautogui.moveTo(self.posSymbolClear)  ;  pyautogui.leftClick()
        pyautogui.moveTo(self.posSymbolPanel)
        if not self.active: return
        pyautogui.doubleClick()
        pyautogui.write(self.symbol)
        pyautogui.press("enter")
        time.sleep(self.waitInput)
        x, y = self.posSymbolTester
        pyautogui.moveTo(self.posSymbolFirst)
        if not self.active: return
        pyautogui.dragTo(x, y, self.waitInput, button = "left")
        if not self.active: return

    def setTest(self):

        pyautogui.moveTo(self.posPropsOpen)  ;  pyautogui.leftClick()  ;  time.sleep(1)
        pyautogui.moveTo(self.posPropsFirst) ;  pyautogui.leftClick()
        if not self.active: return
        while self.paused: pass
        pyautogui.press("home")
        x0 = self.posPropsFirst.x
        y0 = self.posPropsFirst.y
        y1 = self.posPropsSecond.y
        page = 0  ;  time.sleep(1)
        test = self.test.to_dict()
        for label, value in test.items():
            if not self.active: return
            while self.paused: pass
            config = self.config.loc[label, :]
            diff, page = config["page"] - page, config["page"]
            for press in range(diff + 1): pyautogui.press("pgdn")
            pyautogui.moveTo(x0, y0 + (y1 - y0) * config["cell"])
            if not self.active: return
            while self.paused: pass
            if config["type"] in [int, float, str]:
                pyautogui.doubleClick() ; pyautogui.write(str(value))
            if (config["type"] == list):
                for press in range(value): pyautogui.press("down")
            pyautogui.press("enter")
            time.sleep(self.waitInput)
        if not self.active: return
        while self.paused: pass
        pyautogui.moveTo(self.posPropsClose) 
        pyautogui.leftClick()
        time.sleep(self.waitInput)
        pyautogui.moveTo(self.posTesterRun)
        if not self.active: return
        while self.paused: pass
        pyautogui.leftClick()
        time.sleep(0.25) ; pyautogui.keyDown("alt") ; pyautogui.keyDown("tab")
        time.sleep(0.25) ; pyautogui.keyUp("alt")   ; pyautogui.keyUp("tab")
        time.sleep(1)

    def saveResult(self):

        time.sleep(self.waitSave)
        fileName = self.symbol + self.format % (*self.test,)
        for wrong, right in self.corrections.items():
            fileName = fileName.replace(wrong, right)
        if not self.active: return
        while self.paused: pass
        pyautogui.moveTo(self.posResultOpen)  ; pyautogui.leftClick()  ; time.sleep(0.5)
        pyautogui.moveTo(self.posResultPanel) ; pyautogui.rightClick() ; time.sleep(0.5)
        pyautogui.moveTo(self.posResultSave)  ; pyautogui.leftClick()  ; time.sleep(2.0)
        pyautogui.write(fileName)
        if not self.active: return
        while self.paused: pass
        pyautogui.moveTo(self.posSavePath)          ; pyautogui.rightClick() ; time.sleep(0.5)
        [pyautogui.press("down") for _ in range(3)] ; time.sleep(0.5) ; pyautogui.press("enter")
        if not self.active: return
        while self.paused: pass
        pyautogui.write(self.path)          ;  pyautogui.press("enter")  ; time.sleep(0.5)
        pyautogui.moveTo(self.posSaveFile)  ;  pyautogui.leftClick()     ; time.sleep(3)
        if not self.active: return
        while self.paused: pass
        pyautogui.press("left")    ;   time.sleep(0.5)
        if not self.active: return
        while self.paused: pass
        pyautogui.press("enter")   ;   time.sleep(5)
        if not self.active: return
        while self.paused: pass
        pyautogui.leftClick()
        time.sleep(0.5)     ; pyautogui.keyDown("ctrl") ; pyautogui.keyDown("w") 
        time.sleep(0.5)     ; pyautogui.keyUp("ctrl")   ; pyautogui.keyUp("w")
        time.sleep(0.5)     ; pyautogui.keyDown("alt")  ; pyautogui.keyDown("f4")
        time.sleep(0.5)     ; pyautogui.keyUp("alt")    ; pyautogui.keyUp("f4")
        if not self.active: return
        while self.paused: pass
        x, y = self.posResultOpen      ;  posSettings = pyautogui.Point(x // 2, y)
        pyautogui.moveTo(posSettings)  ;  pyautogui.leftClick()
        time.sleep(self.waitSave)

if (__name__ == "__main__"): AutoMQT()