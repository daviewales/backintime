#    Back In Time
#    Copyright (C) 2008-2016 Oprea Dan, Bart de Koning, Richard Bailey, Germar Reitze
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import sys
import os
import gettext
import subprocess
import signal

_=gettext.gettext

if not os.getenv('DISPLAY', ''):
    os.putenv('DISPLAY', ':0.0')

import qt4tools
qt4tools.registerBackintimePath('common')

import tools
import logger
import snapshots
import progress
import logviewdialog
import encfstools

from PyQt4.QtCore import QObject, SIGNAL, QTimer
from PyQt4.QtGui import QSystemTrayIcon, QIcon, QMenu, QProgressBar, QWidget, QRegion


class Qt4SysTrayIcon:
    def __init__(self):
        self.snapshots = snapshots.Snapshots()
        self.config = self.snapshots.config
        self.decode = None

        if len(sys.argv) > 1:
            if not self.config.setCurrentProfile(sys.argv[1]):
                logger.warning("Failed to change Profile_ID %s"
                               %sys.argv[1], self)

        self.qapp = qt4tools.createQApplication(self.config.APP_NAME)
        translator = qt4tools.translator()
        self.qapp.installTranslator(translator)
        self.qapp.setQuitOnLastWindowClosed(False)

        import icon
        self.icon = icon
        self.qapp.setWindowIcon(icon.BIT_LOGO)

        self.status_icon = QSystemTrayIcon(icon.BIT_LOGO)
        #self.status_icon.actionCollection().clear()
        self.contextMenu = QMenu()

        self.menuProfileName = self.contextMenu.addAction(_('Profile: "%s"') % self.config.profileName())
        qt4tools.setFontBold(self.menuProfileName)
        self.contextMenu.addSeparator()

        self.menuStatusMessage = self.contextMenu.addAction(_('Done'))
        self.menuProgress = self.contextMenu.addAction('')
        self.menuProgress.setVisible(False)
        self.contextMenu.addSeparator()

        self.btnPause = self.contextMenu.addAction(icon.PAUSE, _('Pause snapshot process'))
        action = lambda: os.kill(self.snapshots.pid(), signal.SIGSTOP)
        self.btnPause.triggered.connect(action)

        self.btnResume = self.contextMenu.addAction(icon.RESUME, _('Resume snapshot process'))
        action = lambda: os.kill(self.snapshots.pid(), signal.SIGCONT)
        self.btnResume.triggered.connect(action)
        self.btnResume.setVisible(False)

        self.btnStop = self.contextMenu.addAction(icon.STOP, _('Stop snapshot process'))
        self.btnStop.triggered.connect(self.onBtnStop)
        self.contextMenu.addSeparator()

        self.btnDecode = self.contextMenu.addAction(icon.VIEW_SNAPSHOT_LOG, _('decode paths'))
        self.btnDecode.setCheckable(True)
        self.btnDecode.setVisible(self.config.snapshotsMode() == 'ssh_encfs')
        QObject.connect(self.btnDecode, SIGNAL('toggled(bool)'), self.onBtnDecode)

        self.openLog = self.contextMenu.addAction(icon.VIEW_LAST_LOG, _('View Last Log'))
        QObject.connect(self.openLog, SIGNAL('triggered()'), self.onOpenLog)
        self.startBIT = self.contextMenu.addAction(icon.BIT_LOGO, _('Start BackInTime'))
        QObject.connect(self.startBIT, SIGNAL('triggered()'), self.onStartBIT)
        self.status_icon.setContextMenu(self.contextMenu)

        self.pixmap = icon.BIT_LOGO.pixmap(24)
        self.progressBar = QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.resize(24, 6)
        self.progressBar.render(self.pixmap, sourceRegion = QRegion(0, -14, 24, 6), flags = QWidget.RenderFlags(QWidget.DrawChildren))

        self.first_error = self.config.notify()
        self.popup = None
        self.last_message = None

        self.timer = QTimer()
        QObject.connect(self.timer, SIGNAL('timeout()'), self.updateInfo)

        self.ppid = os.getppid()

    def prepairExit(self):
        self.timer.stop()

        if not self.status_icon is None:
            self.status_icon.hide()
            self.status_icon = None

        if not self.popup is None:
            self.popup.deleteLater()
            self.popup = None

        self.qapp.processEvents()

    def run(self):
        self.status_icon.show()
        self.timer.start(500)

        logger.info("[qt4systrayicon] begin loop", self)

        self.qapp.exec_()

        logger.info("[qt4systrayicon] end loop", self)

        self.prepairExit()

    def updateInfo(self):
        if not tools.processAlive(self.ppid):
            self.prepairExit()
            self.qapp.exit(0)
            return

        paused = tools.processPaused(self.snapshots.pid())
        self.btnPause.setVisible(not paused)
        self.btnResume.setVisible(paused)

        message = self.snapshots.takeSnapshotMessage()
        if message is None and self.last_message is None:
            message = (0, _('Working...'))

        if not message is None:
            if message != self.last_message:
                self.last_message = message
                if self.decode:
                    message = (message[0], self.decode.log(message[1]))
                self.menuStatusMessage.setText('\n'.join(tools.wrapLine(message[1],\
                                                                         size = 80,\
                                                                         delimiters = '',\
                                                                         new_line_indicator = '') \
                                                                       ))
                self.status_icon.setToolTip(message[1])

        pg = progress.ProgressFile(self.config)
        if pg.fileReadable():
            pg.load()
            percent = pg.intValue('percent')
            if percent != self.progressBar.value():
                self.progressBar.setValue(percent)
                self.progressBar.render(self.pixmap, sourceRegion = QRegion(0, -14, 24, 6), flags = QWidget.RenderFlags(QWidget.DrawChildren))
                self.status_icon.setIcon(QIcon(self.pixmap))

            self.menuProgress.setText(' | '.join(self.getMenuProgress(pg)))
            self.menuProgress.setVisible(True)
        else:
            self.status_icon.setIcon(self.icon.BIT_LOGO)
            self.menuProgress.setVisible(False)


    def getMenuProgress(self, pg):
        d = (('sent',   _('Sent:')), \
             ('speed',  _('Speed:')),\
             ('eta',    _('ETA:')))
        for key, txt in d:
            value = pg.strValue(key, '')
            if not value:
                continue
            yield txt + ' ' + value

    def onStartBIT(self):
        profileID = self.config.currentProfile()
        cmd = ['backintime-qt4',]
        if not profileID == '1':
            cmd += ['--profile-id', profileID]
        proc = subprocess.Popen(cmd)

    def onOpenLog(self):
        dlg = logviewdialog.LogViewDialog(self, systray = True)
        dlg.decode = self.decode
        dlg.cbDecode.setChecked(self.btnDecode.isChecked())
        dlg.exec_()

    def onBtnDecode(self, checked):
        if checked:
            self.decode = encfstools.Decode(self.config)
            self.last_message = None
            self.updateInfo()
        else:
            self.decode = None

    def onBtnStop(self):
        os.kill(self.snapshots.pid(), signal.SIGKILL)
        self.btnStop.setEnabled(False)
        self.btnPause.setEnabled(False)
        self.btnResume.setEnabled(False)
        self.snapshots.setTakeSnapshotMessage(0, 'Snapshot terminated')

if __name__ == '__main__':
    Qt4SysTrayIcon().run()
