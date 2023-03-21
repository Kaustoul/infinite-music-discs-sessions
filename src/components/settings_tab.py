# -*- coding: utf-8 -*-
#
#Infinite Music Discs settings-tab-specific GUI components module
#Generation tool, datapack design, and resourcepack design by link2_thepast

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal

from src.definitions import Constants, Regexes, ButtonType, SettingType
from src.definitions import SettingsListContents
from src.components.common import QSetsNameFromType, QFocusLineEdit, MultiDragDropButton



#child of QFocusLineEdit, base class for settings LineEdits with drag-drop disabled
class QSettingLineEdit(QFocusLineEdit):
    def supportsFileType(self, ext):
        return False



#child of QSettingLineEdit with integer-only filtering and range limiting
# currently positive integers only
class QPosIntLineEdit(QSettingLineEdit):
    def __init__(self, minInt = 0, maxInt = float('inf'), parent = None):
        super().__init__(text=str(minInt), parent=parent)

        self._min = minInt
        self._max = maxInt

        #create validator to restrict input to integers
        # QRegExpValidator is more flexible than QIntValidator
        regexp = QtCore.QRegExp(Regexes.LE_POS_INT)
        validator = QtGui.QRegExpValidator(regexp)
        self.setValidator(validator)

        self.editingFinished.connect(self.capTop)
        self.editingFinished.connect(self.capBottom)

    def text_int(self):
        try:
            return int(self.text())
        except ValueError:
            return self._min

    def capBottom(self):
        try:
            i_text = int(self.text())
            i_text = max(i_text, self._min)
        except ValueError:
            i_text = self._min

        self.setText(str(i_text))

    def capTop(self):
        try:
            i_text = int(self.text())
            i_text = min(i_text, self._max)
        except ValueError:
            i_text = self._min

        self.setText(str(i_text))



#child of QSettingLineEdit with input filtering
class QAlphaLineEdit(QSettingLineEdit):
    def __init__(self, text, parent = None):
        super().__init__(text=text, parent=parent)

        self._defaultText = text

        #create validator to restrict input to lowercase letters and underscores
        regexp = QtCore.QRegExp(Regexes.LE_ALPHA)
        validator = QtGui.QRegExpValidator(regexp)
        self.setValidator(validator)

        self.editingFinished.connect(self.fillIfEmpty)

    def fillIfEmpty(self):
        if self.text() == "":
            self.setText(self._defaultText)



#TODO: instead of getWidget(), use factory model to cast return type?
class VirtualSettingSelector(QtWidgets.QWidget):

    changed = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent=parent)

        self._parent = parent
        self.changed.connect(self._parent.settingChanged)

    def forceValue(self, value):
        raise NotImplementedError

    def getWidget(self):
        return self._widget

    def getValue(self):
        raise NotImplementedError

class PackPngSettingSelector(VirtualSettingSelector):
    def __init__(self, parent = None):
        super().__init__(parent=parent)

        self._parent.setObjectName("PACKPNG")

        self._widget = MultiDragDropButton(ButtonType.PACKPNG, parent)
        self._widget.multiDragEnter.connect(self._widget.multiDragEnterEvent)
        self._widget.multiDragLeave.connect(self._widget.multiDragLeaveEvent)
        self._widget.multiDrop.connect(self._widget.multiDropEvent)
        self._widget.fileChanged.connect(self.changed)

    def getValue(self):
        return self._widget.getFile()

class CheckSettingSelector(VirtualSettingSelector):
    def __init__(self, parent = None):
        super().__init__(parent=parent)

        self._parent.setObjectName("CHECK")
        self._widget = QtWidgets.QCheckBox(self)

        self._widget.stateChanged.connect(self.changed)

    def forceValue(self, value):
        #block value update from triggering signals, since the update
        #  came internally and not from a user interaction
        self.blockSignals(True)
        self._widget.setChecked(value)
        self.blockSignals(False)

    def getValue(self):
        return self._widget.isChecked()

class NumEntrySettingSelector(VirtualSettingSelector):
    def __init__(self, params, parent = None):
        super().__init__(parent=parent)

        self._parent.setObjectName("NUM_ENTRY")
        self._widget = QPosIntLineEdit(0, params, self)

        self._widget.editingFinished.connect(self.changed)

    def getValue(self):
        return self._widget.text_int()

class TextEntrySettingSelector(VirtualSettingSelector):
    def __init__(self, params, parent = None):
        super().__init__(parent=parent)

        self._parent.setObjectName("TXT_ENTRY")
        self._widget = QAlphaLineEdit(params, self)
        self._widget.setMaxLength(Constants.LINE_EDIT_MAX_CHARS)

        self._widget.editingFinished.connect(self.changed)

    def getValue(self):
        return self._widget.text()

class VirtualDropdownSettingSelector(VirtualSettingSelector):
    def __init__(self, params, parent = None):
        super().__init__(parent=parent)

        if params is None:
            raise TypeError

        self._parent.setObjectName("DROPDOWN")
        self._widget = QtWidgets.QComboBox(self)
        self._widget.view().setMinimumWidth(len(max(params, key=len) * 8))

        self._widget.currentIndexChanged.connect(self.changed)

        #on Linux, the QComboBox QAbstractItemView popup does not automatically hide on window movement.
        #  manually trigger the popup hide if a "window moved" signal is received
        self._parent.windowMoved.connect(self._widget.hidePopup)

class DropdownDictSettingSelector(VirtualDropdownSettingSelector):
    def __init__(self, params, parent = None):
        super().__init__(parent=parent, params=params)

        self._dict = params
        self._widget.addItems(params.keys())

    def getValue(self):
        return self._dict[ self._widget.currentText() ]

class DropdownListSettingSelector(VirtualDropdownSettingSelector):
    def __init__(self, params, parent = None):
        super().__init__(parent=parent, params=params)

        self._widget.addItems(params)

    def getValue(self):
        return self._widget.currentText()



class SettingsListEntry(QtWidgets.QFrame):
    windowMoved = QtCore.pyqtSignal()
    settingChanged = QtCore.pyqtSignal()

    def __init__(self, key, settingType, label, tooltip = None, params = None, parent = None):
        super().__init__(parent=parent)

        self._parent = parent
        self._key = key

        self._label = QtWidgets.QLabel(label)

        if(settingType == SettingType.PACKPNG):         self._selector = PackPngSettingSelector(self)
        elif(settingType == SettingType.CHECK):         self._selector = CheckSettingSelector(self)
        elif(settingType == SettingType.NUM_ENTRY):     self._selector = NumEntrySettingSelector(params, self)
        elif(settingType == SettingType.TXT_ENTRY):     self._selector = TextEntrySettingSelector(params, self)
        elif(settingType == SettingType.DROPDOWN):      self._selector = DropdownDictSettingSelector(params, self)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(5, 5, 5, 5)

        if tooltip is not None:
            self._label.setToolTip(tooltip)
            self._selector._widget.setToolTip(tooltip)

        if not settingType == SettingType.PACKPNG:
            layout.setContentsMargins(50, -1, -1, -1)

        layout.addWidget(self._selector.getWidget())
        layout.addWidget(self._label)
        layout.addStretch(1)

        self.setLayout(layout)

        #provide child SettingsSelector with a "window moved" signal
        #also indicate to parent if setting updated its value
        if self._parent is not None:
            self._parent.windowMoved.connect(self.windowMoved)
            self.settingChanged.connect(self._parent.settingChanged)

        self.setObjectName(key)
        self._label.setObjectName('SettingLabel')

    def forceValue(self, value, locked):
        self._selector.forceValue(value)
        self.setEnabled(not locked)

    def getIndex(self):
        return 0

    def getKeyValue(self):
        return {self._key : self._selector.getValue()}



class SettingsList(QtWidgets.QWidget, QSetsNameFromType):
    windowMoved = QtCore.pyqtSignal()
    settingChanged = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent=parent)

        self._parent = parent

        #child layout, contains settings entries
        self._childLayout = QtWidgets.QVBoxLayout()
        self._childLayout.setSpacing(0)
        self._childLayout.setContentsMargins(1, 1, 1, 1)

        for s in SettingsListContents:
            self._childLayout.addWidget(
                SettingsListEntry(key=s.key, settingType=s.type, label=s.label, tooltip=s.tooltip, params=s.params, parent=self)
            )

        self._childLayout.addStretch()

        #child widget, contains child layout
        widget = QtWidgets.QWidget()
        widget.setLayout(self._childLayout)

        #scroll area, contains child widget and makes child widget scrollable
        scrollArea = QtWidgets.QScrollArea(self)
        scrollArea.setWidget(widget)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        #layout, contains scroll area
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scrollArea)

        self.setLayout(layout)

        #provide settings entries (especially those with QComboBox selectors) with a "window moved" signal
        self._parent.windowMoved.connect(self.windowMoved)
        self.settingChanged.connect(self.settingChangedEvent)

        widget.setObjectName('SettingsChildWidget')
        scrollArea.setObjectName('SettingsScrollArea')

    #TODO: define all these dict keys in definitions
    def settingChangedEvent(self):
        gameVersionEntry = self.findChild(SettingsListEntry, 'version')
        dpVersionEntry = self.findChild(SettingsListEntry, 'legacy_dp')

        gameVersion = gameVersionEntry.getKeyValue()['version']
        dpVersion = dpVersionEntry.getKeyValue()['legacy_dp']

        #lock "legacy datapack" setting to its enabled state if an old game version is selected
        if(dpVersionEntry.isEnabled() and gameVersion['dp'] <= Constants.LEGACY_DP_LATEST_VERSION):
            self.dp_ver = dpVersion
            dpVersionEntry.forceValue(True, locked=True)

        # otherwise, restore original state
        elif(not dpVersionEntry.isEnabled() and gameVersion['dp'] > Constants.LEGACY_DP_LATEST_VERSION):
            dpVersionEntry.forceValue(self.dp_ver, locked=False)

    def getUserSettings(self):
        settingsDict = {}
        for i in range(self._childLayout.count()):
            e = self._childLayout.itemAt(i).widget()

            if(type(e) == SettingsListEntry):
                settingsDict.update(e.getKeyValue())

        return settingsDict


