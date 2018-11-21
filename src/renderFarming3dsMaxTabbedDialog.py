
def rsd_cycle(dialog):
    """
    Attempts to cycle through the tabs in Max's Render Dialog.
    Doesn't work, don't use.  Just keeping it here for posterity's sake
    :param dialog: a 3DS Max Tabbed Dialog
    :return: None
    """
    for i in range(0, len(dialog.get_tabs)):
        dialog.set_current_tab(i)


def cycle_render_dialog(rt):
    """
    Opens cycles through the tabs and then closes the 3DS Max render dialog
    Doesn't work
    :return: None
    """
    rt.renderSceneDialog.open()
    rsd_cycle(TabbedDialog("render", rt))
    rt.renderSceneDialog.close()


class TabbedDialogPage:
    # One page of a tabbed dialog
    # Used for interfacing with Max's goofy tabbed dialog system
    # Stores the class id that max needs to find a tab because an array is too hard I guess
    def __init__(self):

        self._class_id = None
        self._name = str()

    def set_name(self, name):
        self._name = name

    def set_class_id(self, class_id):
        self._class_id = class_id

    def get_name(self):
        return self._name

    def get_class_id(self):
        return self._class_id

    def __str__(self):
        return "{0}, {1}".format(self._name, self._class_id)

    def __repr__(self):
        return self.__str__()


class TabbedDialog:
    # Interfaces with max's tabbed dialog system.
    # doesn't work more than once apparently, probably because Max's
    # garbage collection is crap or something.  Don't use this
    def __init__(self, class_id, rt):
        self._rt = rt

        self._tab_array = list()
        self._id = self._rt.name(class_id)

        dialog_is_open = self._rt.tabbedDialogs.isOpen(self._id)

        if dialog_is_open:
            self._collect_tabs()

    def _collect_tabs(self):
        page_num = self._rt.tabbedDialogs.getNumPages(self._id)

        for i in range(0, page_num):
            class_id = self._rt.tabbedDialogs.getPageID(self._id, i+1)

            tab = TabbedDialogPage()

            tab.set_class_id(str(class_id))

            class_name = self._rt.tabbedDialogs.getPageTitle(self._id, tab.get_class_id())

            tab.set_name(str(class_name))

            self._tab_array.append(tab)

    def collect_tabs(self):
        dialog_is_open = self._rt.tabbedDialogs.isOpen(self._id)

        if dialog_is_open:
            self._collect_tabs()
            return True
        else:
            return False

    def get_tabs(self):
        return self._tab_array

    def set_current_tab(self, index):
        tab = self._tab_array[index]
        self._rt.tabbedDialogs.setCurrentPage(self._id, tab.get_class_id())

    def __str__(self):
        return str(self._tab_array)

    def __repr__(self):
        return self.__str__()
