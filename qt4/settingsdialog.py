#    Back In Time
#    Copyright (C) 2008-2009 Oprea Dan, Bart de Koning, Richard Bailey
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


import os
import os.path
import sys
import datetime
import gettext
import copy
import subprocess

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import config
import tools
import qt4tools
import mount
import password
import messagebox

_=gettext.gettext


class SettingsDialog( QDialog ):
    def __init__( self, parent ):
        QDialog.__init__( self, parent )

        self.parent = parent
        self.config = parent.config
        self.snapshots = parent.snapshots
        self.config_copy_dict = copy.copy( self.config.dict )
        self.current_profile_org = self.config.get_current_profile()
        import icon
        self.icon = icon

        self.setWindowIcon(icon.SETTINGS_DIALOG)
        self.setWindowTitle( _( 'Settings' ) )

        self.main_layout = QVBoxLayout(self)

        #profiles
        layout = QHBoxLayout()
        self.main_layout.addLayout( layout )

        layout.addWidget( QLabel( _('Profile:'), self ) )

        self.first_update_all = True
        self.disable_profile_changed = True
        self.combo_profiles = QComboBox( self )
        layout.addWidget( self.combo_profiles, 1 )
        QObject.connect( self.combo_profiles, SIGNAL('currentIndexChanged(int)'), self.current_profile_changed )
        self.disable_profile_changed = False

        self.btn_edit_profile = QPushButton(icon.PROFILE_EDIT, _('Edit'), self )
        QObject.connect( self.btn_edit_profile, SIGNAL('clicked()'), self.edit_profile )
        layout.addWidget( self.btn_edit_profile )

        self.btn_add_profile = QPushButton(icon.ADD, _('Add'), self)
        QObject.connect( self.btn_add_profile, SIGNAL('clicked()'), self.add_profile )
        layout.addWidget( self.btn_add_profile )

        self.btn_remove_profile = QPushButton(icon.REMOVE, _('Remove'), self)
        QObject.connect( self.btn_remove_profile, SIGNAL('clicked()'), self.remove_profile )
        layout.addWidget( self.btn_remove_profile )

        #TABs
        self.tabs_widget = QTabWidget( self )
        self.main_layout.addWidget( self.tabs_widget )

        #occupy whole space for tabs
        scrollButtonDefault = self.tabs_widget.usesScrollButtons()
        self.tabs_widget.setUsesScrollButtons(False)

        #TAB: General
        tab_widget = QWidget( self )
        self.tabs_widget.addTab( tab_widget, _( 'General' ) )
        layout = QVBoxLayout( tab_widget )
        
        #select mode
        self.mode = None
        vlayout = QVBoxLayout()
        layout.addLayout( vlayout )
        
        self.lbl_modes = QLabel( _( 'Mode:' ), self )
        
        self.combo_modes = QComboBox( self )
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.lbl_modes)
        hlayout.addWidget(self.combo_modes, 1)
        vlayout.addLayout(hlayout)
        store_modes = {}
        for key in list(self.config.SNAPSHOT_MODES.keys()):
            store_modes[key] = self.config.SNAPSHOT_MODES[key][1]
        self.fill_combo( self.combo_modes, store_modes )
        
        #Where to save snapshots
        group_box = QGroupBox( self )
        self.mode_local = group_box
        group_box.setTitle( _( 'Where to save snapshots' ) )
        layout.addWidget( group_box )

        vlayout = QVBoxLayout( group_box )

        hlayout = QHBoxLayout()
        vlayout.addLayout( hlayout )

        self.edit_snapshots_path = QLineEdit( self )
        self.edit_snapshots_path.setReadOnly( True )
        hlayout.addWidget( self.edit_snapshots_path )

        self.btn_snapshots_path = QToolButton(self)
        self.btn_snapshots_path.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.btn_snapshots_path.setIcon(icon.FOLDER)
        self.btn_snapshots_path.setText(_('Folder'))
        self.btn_snapshots_path.setMinimumSize(32,28)
        hlayout.addWidget( self.btn_snapshots_path )
        QObject.connect( self.btn_snapshots_path, SIGNAL('clicked()'), self.on_btn_snapshots_path_clicked )
        
        #SSH
        group_box = QGroupBox( self )
        self.mode_ssh = group_box
        group_box.setTitle( _( 'SSH Settings' ) )
        layout.addWidget( group_box )

        vlayout = QVBoxLayout( group_box )

        hlayout1 = QHBoxLayout()
        vlayout.addLayout( hlayout1 )
        hlayout2 = QHBoxLayout()
        vlayout.addLayout( hlayout2 )
        hlayout3 = QHBoxLayout()
        vlayout.addLayout( hlayout3 )
        
        self.lbl_ssh_host = QLabel( _( 'Host:' ), self )
        hlayout1.addWidget( self.lbl_ssh_host )
        self.txt_ssh_host = QLineEdit( self )
        hlayout1.addWidget( self.txt_ssh_host )
        
        self.lbl_ssh_port = QLabel( _( 'Port:' ), self )
        hlayout1.addWidget( self.lbl_ssh_port )
        self.txt_ssh_port = QLineEdit( self )
        hlayout1.addWidget( self.txt_ssh_port )
        
        self.lbl_ssh_user = QLabel( _( 'User:' ), self )
        hlayout1.addWidget( self.lbl_ssh_user )
        self.txt_ssh_user = QLineEdit( self )
        hlayout1.addWidget( self.txt_ssh_user )
        
        self.lbl_ssh_path = QLabel( _( 'Path:' ), self )
        hlayout2.addWidget( self.lbl_ssh_path )
        self.txt_ssh_path = QLineEdit( self )
        hlayout2.addWidget( self.txt_ssh_path )
        
        self.lbl_ssh_cipher = QLabel( _( 'Cipher:' ), self )
        hlayout3.addWidget( self.lbl_ssh_cipher )
        self.combo_ssh_cipher = QComboBox( self )
        hlayout3.addWidget( self.combo_ssh_cipher )
        self.fill_combo( self.combo_ssh_cipher, self.config.SSH_CIPHERS )
        
        self.lbl_ssh_private_key_file = QLabel( _( 'Private Key:' ), self )
        hlayout3.addWidget( self.lbl_ssh_private_key_file )
        self.txt_ssh_private_key_file = QLineEdit( self )
        self.txt_ssh_private_key_file.setReadOnly( True )
        hlayout3.addWidget( self.txt_ssh_private_key_file )
        
        self.btn_ssh_private_key_file = QToolButton(self)
        self.btn_ssh_private_key_file.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.btn_ssh_private_key_file.setIcon(icon.FOLDER)
        self.btn_ssh_private_key_file.setText(_('Key File'))
        self.btn_ssh_private_key_file.setMinimumSize(32,28)
        hlayout3.addWidget( self.btn_ssh_private_key_file )
        QObject.connect( self.btn_ssh_private_key_file, SIGNAL('clicked()'), self.on_btn_ssh_private_key_file_clicked )
        qt4tools.equal_indent(self.lbl_ssh_host, self.lbl_ssh_path, self.lbl_ssh_cipher)
        
        #encfs
        self.mode_local_encfs = self.mode_local
        self.mode_ssh_encfs = self.mode_ssh
        
##		#Dummy
##		group_box = QGroupBox( self )
##		self.mode_dummy = group_box
##		group_box.setTitle( _( 'Dummy Settings' ) )
##		layout.addWidget( group_box )
##
##		vlayout = QVBoxLayout( group_box )
##
##		hlayout = QHBoxLayout()
##		vlayout.addLayout( hlayout )
##		
##		self.lbl_dummy_host = QLabel( _( 'Host:' ), self )
##		hlayout.addWidget( self.lbl_dummy_host )
##		self.txt_dummy_host = QLineEdit( self )
##		hlayout.addWidget( self.txt_dummy_host )
##		
##		self.lbl_dummy_port = QLabel( _( 'Port:' ), self )
##		hlayout.addWidget( self.lbl_dummy_port )
##		self.txt_dummy_port = QLineEdit( self )
##		hlayout.addWidget( self.txt_dummy_port )
##		
##		self.lbl_dummy_user = QLabel( _( 'User:' ), self )
##		hlayout.addWidget( self.lbl_dummy_user )
##		self.txt_dummy_user = QLineEdit( self )
##		hlayout.addWidget( self.txt_dummy_user )

        #password
        group_box = QGroupBox( self )
        self.frame_password_1 = group_box
        group_box.setTitle( _( 'Password' ) )
        layout.addWidget( group_box )

        vlayout = QVBoxLayout( group_box )
        hlayout1 = QHBoxLayout()
        vlayout.addLayout(hlayout1)
        hlayout2 = QHBoxLayout()
        vlayout.addLayout(hlayout2)

        self.lbl_password_1 = QLabel( _( 'Password' ), self )
        hlayout1.addWidget( self.lbl_password_1 )
        self.txt_password_1 = QLineEdit( self )
        self.txt_password_1.setEchoMode(QLineEdit.Password)
        hlayout1.addWidget( self.txt_password_1 )

        self.lbl_password_2 = QLabel( _( 'Password' ), self )
        hlayout2.addWidget( self.lbl_password_2 )
        self.txt_password_2 = QLineEdit( self )
        self.txt_password_2.setEchoMode(QLineEdit.Password)
        hlayout2.addWidget( self.txt_password_2 )

        self.cb_password_save = QCheckBox( _( 'Save Password to Keyring' ), self )
        vlayout.addWidget( self.cb_password_save )

        self.cb_password_use_cache = QCheckBox( _( 'Cache Password for Cron (Security issue: root can read password)' ), self )
        vlayout.addWidget( self.cb_password_use_cache )

        self.keyring_supported = tools.keyring_supported()
        self.cb_password_save.setEnabled(self.keyring_supported)

        #mode change
        QObject.connect( self.combo_modes, SIGNAL('currentIndexChanged(int)'), self.on_combo_modes_changed )
        
        #host, user, profile id
        group_box = QGroupBox( self )
        self.frame_advanced = group_box
        group_box.setTitle( _( 'Advanced' ) )
        layout.addWidget( group_box )
        
        hlayout = QHBoxLayout( group_box )
        hlayout.addSpacing( 12 )

        vlayout2 = QVBoxLayout()
        hlayout.addLayout( vlayout2 )

        hlayout2 = QHBoxLayout()
        vlayout2.addLayout( hlayout2 )

        self.cb_auto_host_user_profile = QCheckBox( _( 'Auto Host / User / Profile Id' ), self )
        QObject.connect( self.cb_auto_host_user_profile, SIGNAL('stateChanged(int)'), self.update_host_user_profile )
        hlayout2.addWidget( self.cb_auto_host_user_profile )

        hlayout2 = QHBoxLayout()
        vlayout2.addLayout( hlayout2 )

        self.lbl_host = QLabel( _( 'Host:' ), self )
        hlayout2.addWidget( self.lbl_host )
        self.txt_host = QLineEdit( self )
        hlayout2.addWidget( self.txt_host )

        self.lbl_user = QLabel( _( 'User:' ), self )
        hlayout2.addWidget( self.lbl_user )
        self.txt_user = QLineEdit( self )
        hlayout2.addWidget( self.txt_user )

        self.lbl_profile = QLabel( _( 'Profile:' ), self )
        hlayout2.addWidget( self.lbl_profile )
        self.txt_profile = QLineEdit( self )
        hlayout2.addWidget( self.txt_profile )

        #Schedule
        group_box = QGroupBox( self )
        self.global_schedule_group_box = group_box
        group_box.setTitle( _( 'Schedule' ) )
        layout.addWidget( group_box )

        glayout = QGridLayout( group_box )
        glayout.setColumnStretch(1, 2)

        self.combo_automatic_snapshots = QComboBox( self )
        glayout.addWidget( self.combo_automatic_snapshots, 0, 0, 1, 2 )
        self.fill_combo( self.combo_automatic_snapshots, self.config.AUTOMATIC_BACKUP_MODES )

        self.lbl_automatic_snapshots_day = QLabel( _( 'Day:' ), self )
        self.lbl_automatic_snapshots_day.setContentsMargins( 5, 0, 0, 0 )
        self.lbl_automatic_snapshots_day.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        glayout.addWidget( self.lbl_automatic_snapshots_day, 1, 0 )

        self.combo_automatic_snapshots_day = QComboBox( self )
        glayout.addWidget( self.combo_automatic_snapshots_day, 1, 1 )

        for d in range( 1, 29 ):
            self.combo_automatic_snapshots_day.addItem( QIcon(), str(d), d )

        self.lbl_automatic_snapshots_weekday = QLabel( _( 'Weekday:' ), self )
        self.lbl_automatic_snapshots_weekday.setContentsMargins( 5, 0, 0, 0 )
        self.lbl_automatic_snapshots_weekday.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        glayout.addWidget( self.lbl_automatic_snapshots_weekday, 2, 0 )

        self.combo_automatic_snapshots_weekday = QComboBox( self )
        glayout.addWidget( self.combo_automatic_snapshots_weekday, 2, 1 )

        for d in range( 1, 8 ):
            self.combo_automatic_snapshots_weekday.addItem( QIcon(), datetime.date(2011, 11, 6 + d).strftime("%A"), d )

        self.lbl_automatic_snapshots_time = QLabel( _( 'Hour:' ), self )
        self.lbl_automatic_snapshots_time.setContentsMargins( 5, 0, 0, 0 )
        self.lbl_automatic_snapshots_time.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        glayout.addWidget( self.lbl_automatic_snapshots_time, 3, 0 )

        self.combo_automatic_snapshots_time = QComboBox( self )
        glayout.addWidget( self.combo_automatic_snapshots_time, 3, 1 )

        for t in range( 0, 2300, 100 ):
            self.combo_automatic_snapshots_time.addItem( QIcon(), datetime.time( t//100, t%100 ).strftime("%H:%M"), t )

        self.lbl_automatic_snapshots_time_custom = QLabel( _( 'Hours:' ), self )
        self.lbl_automatic_snapshots_time_custom.setContentsMargins( 5, 0, 0, 0 )
        self.lbl_automatic_snapshots_time_custom.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        glayout.addWidget( self.lbl_automatic_snapshots_time_custom, 4, 0 )

        self.txt_automatic_snapshots_time_custom = QLineEdit( self )
        glayout.addWidget( self.txt_automatic_snapshots_time_custom, 4, 1 )

        #anacron
        self.lbl_automatic_snapshots_anacron = QLabel(_('Run Back In Time periodically with anacron. This is useful if the computer is not running regular.'))
        self.lbl_automatic_snapshots_anacron.setWordWrap(True)
        glayout.addWidget(self.lbl_automatic_snapshots_anacron, 5, 0, 1, 2)

        self.lbl_automatic_snapshots_anacron_period = QLabel(_('Frequency in days:'))
        self.lbl_automatic_snapshots_anacron_period.setContentsMargins( 5, 0, 0, 0 )
        self.lbl_automatic_snapshots_anacron_period.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        glayout.addWidget(self.lbl_automatic_snapshots_anacron_period, 7, 0)

        self.sb_automatic_snapshots_anacron_period = QSpinBox(self)
        self.sb_automatic_snapshots_anacron_period.setSingleStep( 1 )
        self.sb_automatic_snapshots_anacron_period.setRange( 1, 10000 )
        glayout.addWidget(self.sb_automatic_snapshots_anacron_period, 7, 1)

        #udev
        self.lbl_automatic_snapshots_udev = QLabel(_('Run Back In Time as soon as the drive is connected (only once every X days).\nYou will be prompted for your sudo password.'))
        self.lbl_automatic_snapshots_udev.setWordWrap(True)
        glayout.addWidget(self.lbl_automatic_snapshots_udev, 6, 0, 1, 2)

        QObject.connect( self.combo_automatic_snapshots, SIGNAL('currentIndexChanged(int)'), self.current_automatic_snapshot_changed )

        #
        layout.addStretch()
        
        #TAB: Include
        tab_widget = QWidget( self )
        self.tabs_widget.addTab( tab_widget, _( 'Include' ) )
        layout = QVBoxLayout( tab_widget )

        self.list_include = QTreeWidget( self )
        self.list_include.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_include.setRootIsDecorated( False )
        #self.list_include.setEditTriggers( QAbstractItemView.NoEditTriggers )
        #self.list_include.setHeaderLabels( [ _('Include folders'), _('Automatic backup') ] )
        self.list_include.setHeaderLabels( [ _('Include files and folders'),
                                            'Count' ] )
        
        self.list_include_header = self.list_include.header()
        self.list_include_header.setResizeMode( 0, QHeaderView.Stretch )
        self.list_include_header.setClickable(True)
        self.list_include_header.setSortIndicatorShown(True)
        self.list_include_header.setSectionHidden(1, True)
        self.list_include.sortItems(1, Qt.AscendingOrder)
        self.list_include_model = self.list_include.model()
        QObject.connect(self.list_include_header,
                        SIGNAL('sortIndicatorChanged(int,Qt::SortOrder)'),
                        self.list_include_model.sort )

        layout.addWidget( self.list_include )
        self.list_include_count = 0

        buttons_layout = QHBoxLayout()
        layout.addLayout( buttons_layout )

        self.btn_include_file_add = QPushButton(icon.ADD, _('Add file'), self)
        buttons_layout.addWidget( self.btn_include_file_add )
        QObject.connect( self.btn_include_file_add, SIGNAL('clicked()'), self.on_btn_include_file_add_clicked )
        
        self.btn_include_add = QPushButton(icon.ADD, _('Add folder'), self)
        buttons_layout.addWidget( self.btn_include_add )
        QObject.connect( self.btn_include_add, SIGNAL('clicked()'), self.on_btn_include_add_clicked )
        
        self.btn_include_remove = QPushButton(icon.REMOVE, _('Remove'), self)
        buttons_layout.addWidget( self.btn_include_remove )
        QObject.connect( self.btn_include_remove, SIGNAL('clicked()'), self.on_btn_include_remove_clicked )

        #TAB: Exclude
        tab_widget = QWidget( self )
        self.tabs_widget.addTab( tab_widget, _( 'Exclude' ) )
        layout = QVBoxLayout( tab_widget )

        label = QLabel( _('<b>Warning:</b> Wildcards (\'foo*\', \'[fF]oo\', \'fo?\') will be ignored with mode \'SSH encrypted\'.\nOnly separate asterisk are allowed (\'foo/*\', \'foo/**/bar\')'), self )
        label.setWordWrap(True)
        self.lbl_ssh_encfs_exclude_warning = label
        layout.addWidget( label )

        self.list_exclude = QTreeWidget( self )
        self.list_exclude.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_exclude.setRootIsDecorated( False )
        self.list_exclude.setHeaderLabels( [ _('Exclude patterns, files or folders') ,
                                            'Count' ] )
        
        self.list_exclude_header = self.list_exclude.header()
        self.list_exclude_header.setResizeMode( 0, QHeaderView.Stretch )
        self.list_exclude_header.setClickable(True)
        self.list_exclude_header.setSortIndicatorShown(True)
        self.list_exclude_header.setSectionHidden(1, True)
        self.list_exclude.sortItems(1, Qt.AscendingOrder)
        self.list_exclude_model = self.list_exclude.model()
        QObject.connect(self.list_exclude_header,
                        SIGNAL('sortIndicatorChanged(int,Qt::SortOrder)'),
                        self.list_exclude_model.sort )

        layout.addWidget( self.list_exclude )
        self.list_exclude_count = 0

        label = QLabel( _('Highly recommended:'), self )
        qt4tools.set_font_bold( label )
        layout.addWidget( label )
        label = QLabel( ', '.join(self.config.DEFAULT_EXCLUDE), self )
        label.setWordWrap(True)
        layout.addWidget( label )
        
        buttons_layout = QHBoxLayout()
        layout.addLayout( buttons_layout )

        self.btn_exclude_add = QPushButton(icon.ADD, _('Add'), self)
        buttons_layout.addWidget( self.btn_exclude_add )
        QObject.connect( self.btn_exclude_add, SIGNAL('clicked()'), self.on_btn_exclude_add_clicked )
        
        self.btn_exclude_file = QPushButton(icon.ADD, _('Add file'), self)
        buttons_layout.addWidget( self.btn_exclude_file )
        QObject.connect( self.btn_exclude_file, SIGNAL('clicked()'), self.on_btn_exclude_file_clicked )
        
        self.btn_exclude_folder = QPushButton(icon.ADD, _('Add folder'), self)
        buttons_layout.addWidget( self.btn_exclude_folder )
        QObject.connect( self.btn_exclude_folder, SIGNAL('clicked()'), self.on_btn_exclude_folder_clicked )
        
        self.btn_exclude_remove = QPushButton(icon.REMOVE, _('Remove'), self)
        buttons_layout.addWidget( self.btn_exclude_remove )
        QObject.connect( self.btn_exclude_remove, SIGNAL('clicked()'), self.on_btn_exclude_remove_clicked )

        #TAB: Auto-remove
        tab_widget = QWidget( self )
        self.tabs_widget.addTab( tab_widget, _( 'Auto-remove' ) )
        layout = QGridLayout( tab_widget )

        #remove old snapshots
        self.cb_remove_older_then = QCheckBox( _( 'Older than:' ), self )
        layout.addWidget( self.cb_remove_older_then, 0, 0 )
        QObject.connect( self.cb_remove_older_then, SIGNAL('stateChanged(int)'), self.update_remove_older_than )

        self.edit_remove_older_then = QSpinBox(self)
        self.edit_remove_older_then.setRange(1, 1000)
        layout.addWidget( self.edit_remove_older_then, 0, 1 )

        self.combo_remove_older_then = QComboBox( self )
        layout.addWidget( self.combo_remove_older_then, 0, 2 )
        self.fill_combo( self.combo_remove_older_then, self.config.REMOVE_OLD_BACKUP_UNITS )

        #min free space
        enabled, value, unit = self.config.get_min_free_space()

        self.cb_min_free_space = QCheckBox( _( 'If free space is less than:' ), self )
        layout.addWidget( self.cb_min_free_space, 1, 0 )
        QObject.connect( self.cb_min_free_space, SIGNAL('stateChanged(int)'), self.update_min_free_space )

        self.edit_min_free_space = QSpinBox(self)
        self.edit_min_free_space.setRange(1, 1000)
        layout.addWidget( self.edit_min_free_space, 1, 1 )

        self.combo_min_free_space = QComboBox( self )
        layout.addWidget( self.combo_min_free_space, 1, 2 )
        self.fill_combo( self.combo_min_free_space, self.config.MIN_FREE_SPACE_UNITS )

        #min free inodes
        self.cb_min_free_inodes = QCheckBox( _('If free inodes is less than:'), self)
        layout.addWidget(self.cb_min_free_inodes, 2, 0)
        QObject.connect( self.cb_min_free_inodes, SIGNAL('stateChanged(int)'), self.update_min_free_inodes)
        
        self.edit_min_free_inodes = QSpinBox(self)
        self.edit_min_free_inodes.setSuffix(' %')
        self.edit_min_free_inodes.setSingleStep( 1 )
        self.edit_min_free_inodes.setRange( 0, 15 )
        layout.addWidget(self.edit_min_free_inodes, 2, 1)
        
        #smart remove
        self.cb_smart_remove = QCheckBox( _( 'Smart remove' ), self )
        layout.addWidget( self.cb_smart_remove, 3, 0 )

        widget = QWidget( self )
        widget.setContentsMargins( 25, 0, 0, 0 )
        layout.addWidget( widget, 4, 0, 1, 3 )

        smlayout = QGridLayout( widget )

        smlayout.addWidget( QLabel( _( 'Keep all snapshots for the last' ), self ), 0, 0 )
        self.edit_keep_all = QSpinBox(self)
        self.edit_keep_all.setRange(1, 10000)
        smlayout.addWidget( self.edit_keep_all, 0, 1 )
        smlayout.addWidget( QLabel( _( 'day(s)' ), self ), 0, 2 )

        smlayout.addWidget( QLabel( _( 'Keep one snapshot per day for the last' ), self ), 1, 0 )
        self.edit_keep_one_per_day = QSpinBox(self)
        self.edit_keep_one_per_day.setRange(1, 10000)
        smlayout.addWidget( self.edit_keep_one_per_day, 1, 1 )
        smlayout.addWidget( QLabel( _( 'day(s)' ), self ), 1, 2 )

        smlayout.addWidget( QLabel( _( 'Keep one snapshot per week for the last' ), self ), 2, 0 )
        self.edit_keep_one_per_week = QSpinBox(self)
        self.edit_keep_one_per_week.setRange(1, 10000)
        smlayout.addWidget( self.edit_keep_one_per_week, 2, 1 )
        smlayout.addWidget( QLabel( _( 'weeks(s)' ), self ), 2, 2 )

        smlayout.addWidget( QLabel( _( 'Keep one snapshot per month for the last' ), self ), 3, 0 )
        self.edit_keep_one_per_month = QSpinBox(self)
        self.edit_keep_one_per_month.setRange(1, 1000)
        smlayout.addWidget( self.edit_keep_one_per_month, 3, 1 )
        smlayout.addWidget( QLabel( _( 'month(s)' ), self ), 3, 2 )

        smlayout.addWidget( QLabel( _( 'Keep one snapshot per year for all years' ), self ), 4, 0, 1, 3 )

        #don't remove named snapshots
        self.cb_dont_remove_named_snapshots = QCheckBox( _( 'Don\'t remove named snapshots' ), self )
        layout.addWidget( self.cb_dont_remove_named_snapshots, 5, 0, 1, 3 )

        #
        layout.addWidget( QWidget(), 6, 0 )
        layout.setRowStretch( 6, 2 )
        
        #TAB: Options
        tab_widget = QWidget( self )
        self.tabs_widget.addTab( tab_widget, _( 'Options' ) )
        layout = QVBoxLayout( tab_widget )

        self.cb_notify_enabled = QCheckBox( _( 'Enable notifications' ), self )
        layout.addWidget( self.cb_notify_enabled )

        self.cb_no_on_battery = QCheckBox( _( 'Disable snapshots when on battery' ), self )
        if not tools.power_status_available ():
            self.cb_no_on_battery.setEnabled ( False )
            self.cb_no_on_battery.setToolTip ( _( 'Power status not available from system' ) )
        layout.addWidget( self.cb_no_on_battery )

        self.cb_backup_on_restore = QCheckBox( _( 'Backup files on restore' ), self )
        layout.addWidget( self.cb_backup_on_restore )

        self.cb_continue_on_errors = QCheckBox( _( 'Continue on errors (keep incomplete snapshots)' ), self )
        layout.addWidget( self.cb_continue_on_errors )

        self.cb_use_checksum = QCheckBox( _( 'Use checksum to detect changes' ), self )
        layout.addWidget( self.cb_use_checksum )

        self.cb_full_rsync = QCheckBox( _( 'Full rsync mode. May be faster but:' ), self )
        label = QLabel( _('- snapshots are no read-only\n- destination file-system must support all linux attributes (dates, rights, user, group ...)'), self)
        label.setIndent(36)
        label.setWordWrap(True)
        QObject.connect( self.cb_full_rsync, SIGNAL('stateChanged(int)'), self.update_check_for_changes )
        layout.addWidget( self.cb_full_rsync )
        layout.addWidget( label )

        self.cb_check_for_changes = QCheckBox( _( 'Check for changes (don\'t take a new snapshot if nothing changed)' ), self )
        layout.addWidget( self.cb_check_for_changes )

        #log level
        hlayout = QHBoxLayout()
        layout.addLayout( hlayout )

        hlayout.addWidget( QLabel( _('Log Level:'), self ) )

        self.combo_log_level = QComboBox( self )
        hlayout.addWidget( self.combo_log_level, 1 )
        
        self.combo_log_level.addItem( QIcon(), _('None'), 0 )
        self.combo_log_level.addItem( QIcon(), _('Errors'), 1 )
        self.combo_log_level.addItem( QIcon(), _('Changes & Errors'), 2 )
        self.combo_log_level.addItem( QIcon(), _('All'), 3 )

        #
        layout.addStretch()

        #TAB: Expert Options
        tab_widget = QWidget( self )
        self.tabs_widget.addTab( tab_widget, _( 'Expert Options' ) )
        layout = QVBoxLayout( tab_widget )

        label = QLabel( _('Change these options only if you really know what you are doing !'), self )
        qt4tools.set_font_bold( label )
        layout.addWidget( label )

        #self.cb_per_diretory_schedule = QCheckBox( _( 'Enable schedule per included folder (see Include tab; default: disabled)' ), self )
        #layout.addWidget( self.cb_per_diretory_schedule )
        #QObject.connect( self.cb_per_diretory_schedule, SIGNAL('clicked()'), self.update_include_columns )

        self.cb_run_nice_from_cron = QCheckBox( _( 'Run \'nice\' as cron job (default: enabled)' ), self )
        layout.addWidget( self.cb_run_nice_from_cron )

        self.cb_run_ionice_from_cron = QCheckBox( _( 'Run \'ionice\' as cron job (default: enabled)' ), self )
        layout.addWidget( self.cb_run_ionice_from_cron )

        self.cb_run_ionice_from_user = QCheckBox( _( 'Run \'ionice\' when taking a manual snapshot (default: disabled)' ), self )
        layout.addWidget( self.cb_run_ionice_from_user )

        self.cb_run_nice_on_remote = QCheckBox( _('Run \'nice\' on remote host (default: disabled)'), self)
        layout.addWidget(self.cb_run_nice_on_remote)

        self.cb_run_ionice_on_remote = QCheckBox( _('Run \'ionice\' on remote host (default: disabled)'), self)
        layout.addWidget(self.cb_run_ionice_on_remote)

        #bwlimit
        hlayout = QHBoxLayout()
        layout.addLayout(hlayout)
        self.cb_bwlimit = QCheckBox( _( 'Limit rsync bandwidth usage: ' ), self )
        hlayout.addWidget( self.cb_bwlimit )
        self.sb_bwlimit = QSpinBox(self)
        self.sb_bwlimit.setSuffix(  _(' KB/sec') )
        self.sb_bwlimit.setSingleStep( 100 )
        self.sb_bwlimit.setRange( 0, 1000000 )
        hlayout.addWidget(self.sb_bwlimit)
        hlayout.addStretch()

        self.cb_preserve_acl = QCheckBox( _( 'Preserve ACL' ), self )
        layout.addWidget( self.cb_preserve_acl )

        self.cb_preserve_xattr = QCheckBox( _( 'Preserve extended attributes (xattr)' ), self )
        layout.addWidget( self.cb_preserve_xattr )

        self.cb_copy_unsafe_links = QCheckBox( _( 'Copy unsafe links (works only with absolute links)' ), self )
        layout.addWidget( self.cb_copy_unsafe_links )

        self.cb_copy_links = QCheckBox( _( 'Copy links (dereference symbolic links)' ), self )
        layout.addWidget( self.cb_copy_links )

        #
        layout.addStretch()

        #buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent = self)
        QObject.connect(button_box, SIGNAL('accepted()'), self.accept)
        QObject.connect(button_box, SIGNAL('rejected()'), self.reject)
        self.main_layout.addWidget(button_box)

        self.update_profiles()
        self.on_combo_modes_changed()

        #enable tabs scroll buttons again but keep dialog size
        size = self.sizeHint()
        self.tabs_widget.setUsesScrollButtons(scrollButtonDefault)
        self.resize(size)

    def add_profile( self ):
        ret_val =  QInputDialog.getText(self, _('New profile'), str() )
        if not ret_val[1]:
            return

        name = ret_val[0].strip()
        if len( name ) <= 0:
            return

        profile_id = self.config.add_profile( name )
        if profile_id is None:
            return

        self.config.set_current_profile( profile_id )
        self.update_profiles()

    def edit_profile( self ):
        ret_val =  QInputDialog.getText(self, _('Rename profile'), str() )
        if not ret_val[1]:
            return

        name = ret_val[0].strip()
        if len( name ) <= 0:
            return

        if not self.config.set_profile_name( name ):
            return

        self.update_profiles()

    def remove_profile( self ):
        if self.question_handler( _('Are you sure you want to delete the profile "%s" ?') % self.config.get_profile_name() ):
            self.config.remove_profile()
            self.update_profiles()

    def update_automatic_snapshot_time( self, backup_mode ):
        if backup_mode == self.config.CUSTOM_HOUR:
            self.lbl_automatic_snapshots_time_custom.show()
            self.txt_automatic_snapshots_time_custom.show()
        else:
            self.lbl_automatic_snapshots_time_custom.hide()
            self.txt_automatic_snapshots_time_custom.hide()

        if backup_mode == self.config.WEEK:
            self.lbl_automatic_snapshots_weekday.show()
            self.combo_automatic_snapshots_weekday.show()
        else:
            self.lbl_automatic_snapshots_weekday.hide()
            self.combo_automatic_snapshots_weekday.hide()

        if backup_mode == self.config.MONTH:
            self.lbl_automatic_snapshots_day.show()
            self.combo_automatic_snapshots_day.show()
        else:
            self.lbl_automatic_snapshots_day.hide()
            self.combo_automatic_snapshots_day.hide()

        if backup_mode >= self.config.DAY:
            self.lbl_automatic_snapshots_time.show()
            self.combo_automatic_snapshots_time.show()
        else:
            self.lbl_automatic_snapshots_time.hide()
            self.combo_automatic_snapshots_time.hide()

        if self.config.DAY_ANACRON <= backup_mode <= self.config.UDEV:
            self.lbl_automatic_snapshots_anacron_period.show()
            self.sb_automatic_snapshots_anacron_period.show()
            self.lbl_automatic_snapshots_time.hide()
            self.combo_automatic_snapshots_time.hide()
        else:
            self.lbl_automatic_snapshots_anacron_period.hide()
            self.sb_automatic_snapshots_anacron_period.hide()

        if backup_mode == self.config.DAY_ANACRON:
            self.lbl_automatic_snapshots_anacron.show()
        else:
            self.lbl_automatic_snapshots_anacron.hide()

        if backup_mode == self.config.UDEV:
            self.lbl_automatic_snapshots_udev.show()
        else:
            self.lbl_automatic_snapshots_udev.hide()

    def current_automatic_snapshot_changed( self, index ):
        backup_mode = self.combo_automatic_snapshots.itemData( index )
        self.update_automatic_snapshot_time( backup_mode )

    def current_profile_changed( self, index ):
        if self.disable_profile_changed:
            return

        profile_id = str( self.combo_profiles.itemData( index ) )
        if len( profile_id ) <= 0:
            return
        
        if profile_id != self.config.get_current_profile():
            self.save_profile()
            self.config.set_current_profile( profile_id )
            self.update_profile()

    def update_host_user_profile( self ):
        enabled = not self.cb_auto_host_user_profile.isChecked()
        self.lbl_host.setEnabled( enabled )
        self.txt_host.setEnabled( enabled )
        self.lbl_user.setEnabled( enabled )
        self.txt_user.setEnabled( enabled )
        self.lbl_profile.setEnabled( enabled )
        self.txt_profile.setEnabled( enabled )

    def update_check_for_changes(self):
        enabled = not self.cb_full_rsync.isChecked()
        self.cb_check_for_changes.setEnabled( enabled )

    def update_profiles( self ):
        self.update_profile()
        current_profile_id = self.config.get_current_profile()

        self.disable_profile_changed = True

        self.combo_profiles.clear()
            
        profiles = self.config.get_profiles_sorted_by_name()
        for profile_id in profiles:
            self.combo_profiles.addItem( self.config.get_profile_name( profile_id ), profile_id )
            if profile_id == current_profile_id:
                self.combo_profiles.setCurrentIndex( self.combo_profiles.count() - 1 )

        self.disable_profile_changed = False

    def update_profile( self ):
        if self.config.get_current_profile() == '1':
            self.btn_edit_profile.setEnabled( False )
            self.btn_remove_profile.setEnabled( False )
        else:
            self.btn_edit_profile.setEnabled( True )
            self.btn_remove_profile.setEnabled( True )

        #TAB: General
        #mode
        self.set_combo_value( self.combo_modes, self.config.get_snapshots_mode(), type = 'str' )
        
        #local
        self.edit_snapshots_path.setText( self.config.get_snapshots_path( mode = 'local') )
        
        #ssh
        self.txt_ssh_host.setText( self.config.get_ssh_host() )
        self.txt_ssh_port.setText( str(self.config.get_ssh_port()) )
        self.txt_ssh_user.setText( self.config.get_ssh_user() )
        self.txt_ssh_path.setText( self.config.get_snapshots_path_ssh() )
        self.set_combo_value( self.combo_ssh_cipher, self.config.get_ssh_cipher(), type = 'str' )
        self.txt_ssh_private_key_file.setText( self.config.get_ssh_private_key_file() )
        
        #local_encfs
        if self.mode == 'local_encfs':
            self.edit_snapshots_path.setText( self.config.get_local_encfs_path() )
        
##		#dummy
##		self.txt_dummy_host.setText( self.config.get_dummy_host() )
##		self.txt_dummy_port.setText( self.config.get_dummy_port() )
##		self.txt_dummy_user.setText( self.config.get_dummy_user() )

        #password
        password_1 = self.config.get_password( mode = self.mode, pw_id = 1, only_from_keyring = True )
        password_2 = self.config.get_password( mode = self.mode, pw_id = 2, only_from_keyring = True )
        if password_1 is None:
            password_1 = ''
        if password_2 is None:
            password_2 = ''
        self.txt_password_1.setText( password_1 )
        self.txt_password_2.setText( password_2 )
        self.cb_password_save.setChecked( self.keyring_supported and self.config.get_password_save( mode = self.mode ) )
        self.cb_password_use_cache.setChecked( self.config.get_password_use_cache( mode = self.mode ) )

        self.cb_auto_host_user_profile.setChecked( self.config.get_auto_host_user_profile() )
        host, user, profile = self.config.get_host_user_profile()
        self.txt_host.setText( host )
        self.txt_user.setText( user )
        self.txt_profile.setText( profile )
        self.update_host_user_profile()

        self.set_combo_value( self.combo_automatic_snapshots, self.config.get_automatic_backup_mode() )
        self.set_combo_value( self.combo_automatic_snapshots_time, self.config.get_automatic_backup_time() )
        self.set_combo_value( self.combo_automatic_snapshots_day, self.config.get_automatic_backup_day() )
        self.set_combo_value( self.combo_automatic_snapshots_weekday, self.config.get_automatic_backup_weekday() )
        self.txt_automatic_snapshots_time_custom.setText( self.config.get_custom_backup_time() )
        self.sb_automatic_snapshots_anacron_period.setValue(self.config.get_automatic_backup_anacron_period())
        self.update_automatic_snapshot_time( self.config.get_automatic_backup_mode() )

        #TAB: Include
        self.list_include.clear()

        for include in self.config.get_include():
            self.add_include( include )

        #TAB: Exclude
        self.list_exclude.clear()
    
        for exclude in self.config.get_exclude():
            self.add_exclude( exclude )

        #TAB: Auto-remove

        #remove old snapshots
        enabled, value, unit = self.config.get_remove_old_snapshots()
        self.cb_remove_older_then.setChecked( enabled )
        self.edit_remove_older_then.setValue( value )
        self.set_combo_value( self.combo_remove_older_then, unit )

        #min free space
        enabled, value, unit = self.config.get_min_free_space()
        self.cb_min_free_space.setChecked( enabled )
        self.edit_min_free_space.setValue( value )
        self.set_combo_value( self.combo_min_free_space, unit )

        #min free inodes
        self.cb_min_free_inodes.setChecked(self.config.min_free_inodes_enabled())
        self.edit_min_free_inodes.setValue(self.config.min_free_inodes())

        #smart remove
        smart_remove, keep_all, keep_one_per_day, keep_one_per_week, keep_one_per_month = self.config.get_smart_remove()
        self.cb_smart_remove.setChecked( smart_remove )
        self.edit_keep_all.setValue( keep_all )
        self.edit_keep_one_per_day.setValue( keep_one_per_day )
        self.edit_keep_one_per_week.setValue( keep_one_per_week )
        self.edit_keep_one_per_month.setValue( keep_one_per_month )

        #don't remove named snapshots
        self.cb_dont_remove_named_snapshots.setChecked( self.config.get_dont_remove_named_snapshots() )

        #TAB: Options
        self.cb_notify_enabled.setChecked( self.config.is_notify_enabled() )
        self.cb_backup_on_restore.setChecked( self.config.is_backup_on_restore_enabled() )
        self.cb_continue_on_errors.setChecked( self.config.continue_on_errors() )
        self.cb_use_checksum.setChecked( self.config.use_checksum() )
        self.cb_full_rsync.setChecked( self.config.full_rsync() )
        self.update_check_for_changes()
        self.cb_check_for_changes.setChecked( self.config.check_for_changes() )
        self.set_combo_value( self.combo_log_level, self.config.log_level() )

        #TAB: Expert Options
        #self.cb_per_diretory_schedule.setChecked( self.config.get_per_directory_schedule() )
        self.cb_run_nice_from_cron.setChecked( self.config.is_run_nice_from_cron_enabled() )
        self.cb_run_ionice_from_cron.setChecked( self.config.is_run_ionice_from_cron_enabled() )
        self.cb_run_ionice_from_user.setChecked( self.config.is_run_ionice_from_user_enabled() )
        self.cb_run_nice_on_remote.setChecked(self.config.is_run_nice_on_remote_enabled())
        self.cb_run_ionice_on_remote.setChecked(self.config.is_run_ionice_on_remote_enabled())
        self.cb_bwlimit.setChecked( self.config.bwlimit_enabled() )
        self.sb_bwlimit.setValue( self.config.bwlimit() )
        self.cb_no_on_battery.setChecked( self.config.is_no_on_battery_enabled() )
        self.cb_preserve_acl.setChecked( self.config.preserve_acl() )
        self.cb_preserve_xattr.setChecked( self.config.preserve_xattr() )
        self.cb_copy_unsafe_links.setChecked( self.config.copy_unsafe_links() )
        self.cb_copy_links.setChecked( self.config.copy_links() )

        #update
        #self.update_include_columns()
        self.update_remove_older_than()
        self.update_min_free_space()

    def save_profile( self ):
        if self.combo_automatic_snapshots.itemData( self.combo_automatic_snapshots.currentIndex() ) == self.config.CUSTOM_HOUR:
            if not tools.check_cron_pattern(self.txt_automatic_snapshots_time_custom.text() ):
                self.error_handler( _('Custom Hours can only be a comma seperate list of hours (e.g. 8,12,18,23) or */3 for periodic backups every 3 hours') )
                return False
            
        #mode
        mode = str( self.combo_modes.itemData( self.combo_modes.currentIndex() ) )
        self.config.set_snapshots_mode( mode )
        mount_kwargs = {}
        
        #password
        password_1 = self.txt_password_1.text()
        password_2 = self.txt_password_2.text()
        
        #ssh
        ssh_host = self.txt_ssh_host.text()
        ssh_port = self.txt_ssh_port.text()
        ssh_user = self.txt_ssh_user.text()
        ssh_path = self.txt_ssh_path.text()
        ssh_cipher = self.combo_ssh_cipher.itemData( self.combo_ssh_cipher.currentIndex() )
        ssh_private_key_file = self.txt_ssh_private_key_file.text()
        if mode == 'ssh':
            mount_kwargs = {'host': ssh_host,
                            'port': int(ssh_port),
                            'user': ssh_user,
                            'path': ssh_path,
                            'cipher': ssh_cipher,
                            'private_key_file': ssh_private_key_file,
                            'password': password_1
                            }
        
        #local-encfs settings
        local_encfs_path = self.edit_snapshots_path.text()
        if mode == 'local_encfs':
            mount_kwargs = {'path': local_encfs_path,
                            'password': password_1
                            }
        
        #ssh_encfs settings
        if mode == 'ssh_encfs':
            mount_kwargs = {'host': ssh_host,
                            'port': int(ssh_port),
                            'user': ssh_user,
                            'ssh_path': ssh_path,
                            'cipher': ssh_cipher,
                            'private_key_file': ssh_private_key_file,
                            'ssh_password': password_1,
                            'encfs_password': password_2
                            }

##		#dummy
##		dummy_host = self.txt_dummy_host.text()
##		dummy_port = self.txt_dummy_port.text()
##		dummy_user = self.txt_dummy_user.text()
##		if mode == 'dummy':
##			#values must have exactly the same Type (str, int or bool) 
##			#as they are set in config or you will run into false-positive
##			#HashCollision warnings
##			mount_kwargs = {'host': dummy_host,
##							'port': int(dummy_port),
##							'user': dummy_user,
##							'password': password_1
##							}
            
        if not self.config.SNAPSHOT_MODES[mode][0] is None:
            #pre_mount_check
            mnt = mount.Mount(cfg = self.config, tmp_mount = True, parent = self)
            try:
                mnt.pre_mount_check(mode = mode, first_run = True, **mount_kwargs)
            except mount.MountException as ex:
                self.error_handler(str(ex))
                return False

            #okay, lets try to mount
            try:
                hash_id = mnt.mount(mode = mode, check = False, **mount_kwargs)
            except mount.MountException as ex:
                self.error_handler(str(ex))
                return False
        
        #snapshots path
        self.config.set_auto_host_user_profile( self.cb_auto_host_user_profile.isChecked() )
        self.config.set_host_user_profile(
                self.txt_host.text(),
                self.txt_user.text(),
                self.txt_profile.text() )
                
        if self.config.SNAPSHOT_MODES[mode][0] is None:
            snapshots_path = self.edit_snapshots_path.text()
        else:
            snapshots_path = self.config.get_snapshots_path(mode = mode, tmp_mount = True)
            
        self.config.set_snapshots_path( snapshots_path, mode = mode )
        
        #save ssh
        self.config.set_ssh_host(ssh_host)
        self.config.set_ssh_port(ssh_port)
        self.config.set_ssh_user(ssh_user)
        self.config.set_snapshots_path_ssh(ssh_path)
        self.config.set_ssh_cipher(ssh_cipher)
        self.config.set_ssh_private_key_file(ssh_private_key_file)
        
        #save local_encfs
        self.config.set_local_encfs_path(local_encfs_path)
        
##		#save dummy
##		self.config.set_dummy_host(dummy_host)
##		self.config.set_dummy_port(dummy_port)
##		self.config.set_dummy_user(dummy_user)

        #save password
        self.config.set_password_save(self.cb_password_save.isChecked(), mode = mode)
        self.config.set_password_use_cache(self.cb_password_use_cache.isChecked(), mode = mode)
        self.config.set_password(password_1, mode = mode)
        self.config.set_password(password_2, mode = mode, pw_id = 2)

        #include list 
        self.list_include.sortItems(1, Qt.AscendingOrder)
        include_list = []
        for index in range( self.list_include.topLevelItemCount() ):
            item = self.list_include.topLevelItem( index )
            #include_list.append( [ item.text(0), item.data( 0, Qt.UserRole ) ] )
            include_list.append( ( item.text(0), item.data( 0, Qt.UserRole ) ) )
        
        self.config.set_include( include_list )

        #exclude patterns
        self.list_exclude.sortItems(1, Qt.AscendingOrder)
        exclude_list = []
        for index in range( self.list_exclude.topLevelItemCount() ):
            item = self.list_exclude.topLevelItem( index )
            exclude_list.append( item.text(0) )

        self.config.set_exclude( exclude_list )

        #schedule
        self.config.set_automatic_backup_mode( self.combo_automatic_snapshots.itemData( self.combo_automatic_snapshots.currentIndex() ) )
        self.config.set_automatic_backup_time( self.combo_automatic_snapshots_time.itemData( self.combo_automatic_snapshots_time.currentIndex() ) )
        self.config.set_automatic_backup_weekday( self.combo_automatic_snapshots_weekday.itemData( self.combo_automatic_snapshots_weekday.currentIndex() ) )
        self.config.set_automatic_backup_day( self.combo_automatic_snapshots_day.itemData( self.combo_automatic_snapshots_day.currentIndex() ) )
        self.config.set_custom_backup_time( self.txt_automatic_snapshots_time_custom.text() )
        self.config.set_automatic_backup_anacron_period(self.sb_automatic_snapshots_anacron_period.value())

        #auto-remove
        self.config.set_remove_old_snapshots( 
                        self.cb_remove_older_then.isChecked(), 
                        self.edit_remove_older_then.value(),
                        self.combo_remove_older_then.itemData( self.combo_remove_older_then.currentIndex() ) )
        self.config.set_min_free_space( 
                        self.cb_min_free_space.isChecked(), 
                        self.edit_min_free_space.value(),
                        self.combo_min_free_space.itemData( self.combo_min_free_space.currentIndex() ) )
        self.config.set_min_free_inodes(
                        self.cb_min_free_inodes.isChecked(),
                        self.edit_min_free_inodes.value() )
        self.config.set_dont_remove_named_snapshots( self.cb_dont_remove_named_snapshots.isChecked() )
        self.config.set_smart_remove( 
                        self.cb_smart_remove.isChecked(),
                        self.edit_keep_all.value(),
                        self.edit_keep_one_per_day.value(),
                        self.edit_keep_one_per_week.value(),
                        self.edit_keep_one_per_month.value() )

        #options
        self.config.set_notify_enabled( self.cb_notify_enabled.isChecked() )
        self.config.set_backup_on_restore( self.cb_backup_on_restore.isChecked() )
        self.config.set_continue_on_errors( self.cb_continue_on_errors.isChecked() )
        self.config.set_use_checksum( self.cb_use_checksum.isChecked() )
        self.config.set_full_rsync( self.cb_full_rsync.isChecked() )
        self.config.set_check_for_changes( self.cb_check_for_changes.isChecked() )
        self.config.set_log_level( self.combo_log_level.itemData( self.combo_log_level.currentIndex() ) )

        #expert options
        #self.config.set_per_directory_schedule( self.cb_per_diretory_schedule.isChecked() )
        self.config.set_run_nice_from_cron_enabled( self.cb_run_nice_from_cron.isChecked() )
        self.config.set_run_ionice_from_cron_enabled( self.cb_run_ionice_from_cron.isChecked() )
        self.config.set_run_ionice_from_user_enabled( self.cb_run_ionice_from_user.isChecked() )
        self.config.set_run_nice_on_remote_enabled(self.cb_run_nice_on_remote.isChecked())
        self.config.set_run_ionice_on_remote_enabled(self.cb_run_ionice_on_remote.isChecked())
        self.config.set_bwlimit_enabled( self.cb_bwlimit.isChecked() )
        self.config.set_bwlimit( self.sb_bwlimit.value() )
        self.config.set_no_on_battery_enabled( self.cb_no_on_battery.isChecked() )
        self.config.set_preserve_acl( self.cb_preserve_acl.isChecked() )
        self.config.set_preserve_xattr( self.cb_preserve_xattr.isChecked() )
        self.config.set_copy_unsafe_links( self.cb_copy_unsafe_links.isChecked() )
        self.config.set_copy_links( self.cb_copy_links.isChecked() )
        
        #umount
        if not self.config.SNAPSHOT_MODES[mode][0] is None:
            try:
                mnt.umount(hash_id = hash_id)
            except mount.MountException as ex:
                self.error_handler(str(ex))
                return False
        return True

    def error_handler( self, message ):
        messagebox.critical( self, message )

    def question_handler( self, message ):
        return QMessageBox.Yes == messagebox.warningYesNo( self, message )

    def exec_( self ):
        self.config.set_question_handler( self.question_handler )
        self.config.set_error_handler( self.error_handler )
        ret_val = QDialog.exec_( self )
        self.config.clear_handlers()

        if ret_val != QDialog.Accepted:
            self.config.dict = self.config_copy_dict
            
        self.config.set_current_profile( self.current_profile_org )

        return ret_val

    def update_snapshots_location( self ):
        '''Update snapshot location dialog'''
        self.config.set_question_handler( self.question_handler )
        self.config.set_error_handler( self.error_handler )
        self.snapshots.update_snapshots_location()
    
    #def update_include_columns( self ):
    #	if self.cb_per_diretory_schedule.isChecked():
    #		self.list_include.showColumn( 1 )
    #		self.global_schedule_group_box.hide()
    #	else:
    #		self.list_include.hideColumn( 1 )
    #		self.global_schedule_group_box.show()

    #def on_list_include_item_activated( self, item, column ):
    #	if not self.cb_per_diretory_schedule.isChecked():
    #		return
    #	
    #	if item is None:
    #		return

    #	#if column != 1:
    #	#	return

    #	self.popup_automatic_backup.popup( QCursor.pos() )

    #def on_popup_automatic_backup( self ):
    #	print "ABC"

    def update_remove_older_than( self ):
        enabled = self.cb_remove_older_then.isChecked()
        self.edit_remove_older_then.setEnabled( enabled )
        self.combo_remove_older_then.setEnabled( enabled )

    def update_min_free_space( self ):
        enabled = self.cb_min_free_space.isChecked()
        self.edit_min_free_space.setEnabled( enabled )
        self.combo_min_free_space.setEnabled( enabled )

    def update_min_free_inodes(self):
        enabled = self.cb_min_free_inodes.isChecked()
        self.edit_min_free_inodes.setEnabled(enabled)

    def add_include( self, data ):
        item = QTreeWidgetItem()

        if data[1] == 0:
            item.setIcon(0, self.icon.FOLDER)
        else:
            item.setIcon(0, self.icon.FILE)

        item.setText( 0, data[0] )
        #item.setText( 0, data[0] )
        #item.setText( 1, self.config.AUTOMATIC_BACKUP_MODES[ data[1] ] )
        item.setData( 0, Qt.UserRole, data[1] )
        self.list_include_count += 1
        item.setText(1, str(self.list_include_count).zfill(6))
        item.setData(1, Qt.UserRole, self.list_include_count )
        self.list_include.addTopLevelItem( item )

        if self.list_include.currentItem() is None:
            self.list_include.setCurrentItem( item )

        return item

    def add_exclude( self, pattern ):
        item = QTreeWidgetItem()
        item.setIcon(0, self.icon.EXCLUDE)
        item.setText(0, pattern)
        item.setData(0, Qt.UserRole, pattern )
        self.list_exclude_count += 1
        item.setText(1, str(self.list_exclude_count).zfill(6))
        item.setData(1, Qt.UserRole, self.list_exclude_count )
        self.list_exclude.addTopLevelItem(item)

        if self.list_exclude.currentItem() is None:
            self.list_exclude.setCurrentItem( item )

        return item

    def fill_combo( self, combo, dict ):
        keys = list(dict.keys())
        keys.sort()

        for key in keys:
            combo.addItem( QIcon(), dict[ key ], key )

    def set_combo_value( self, combo, value, type = 'int' ):
        for i in range( combo.count() ):
            if type == 'int' and value == combo.itemData( i ):
                combo.setCurrentIndex( i )
                break
            if type == 'str' and value == combo.itemData( i ):
                combo.setCurrentIndex( i )
                break

    def validate( self ):
        if not self.save_profile():
            return False

        if not self.config.check_config():
            return False

        if not self.config.setup_cron():
            return False

        self.config.save()
        return True

    def on_btn_exclude_remove_clicked ( self ):
        for item in self.list_exclude.selectedItems():
            index = self.list_exclude.indexOfTopLevelItem( item )
            if index < 0:
                continue

            self.list_exclude.takeTopLevelItem( index )

        if self.list_exclude.topLevelItemCount() > 0:
            self.list_exclude.setCurrentItem( self.list_exclude.topLevelItem(0) )

    def add_exclude_( self, pattern ):
        if len( pattern ) == 0:
            return

        for index in range( self.list_exclude.topLevelItemCount() ):
            item = self.list_exclude.topLevelItem( index )
            if pattern == item.text(0):
                return

        self.add_exclude( pattern )
    
    def on_btn_exclude_add_clicked( self ):
        ret_val = QInputDialog.getText(self, _('Exclude pattern'), str() )
        if not ret_val[1]:
            return

        pattern = ret_val[0].strip()

        if len( pattern ) == 0:
            return

        if pattern.find( ':' ) >= 0:
            messagebox.critical( self, _('Exclude patterns can\'t contain \':\' char !') )
            return
    
        self.add_exclude_( pattern )

    def on_btn_exclude_file_clicked( self ):
        for path in qt4tools.getOpenFileNames(self, _('Exclude file')):
            self.add_exclude_( path )

    def on_btn_exclude_folder_clicked( self ):
        for path in qt4tools.getExistingDirectories(self, _('Exclude folder')) :
            self.add_exclude_( path )

    def on_btn_include_remove_clicked ( self ):
        for item in self.list_include.selectedItems():
            index = self.list_include.indexOfTopLevelItem( item )
            if index < 0:
                continue

            self.list_include.takeTopLevelItem( index )

        if self.list_include.topLevelItemCount() > 0:
            self.list_include.setCurrentItem( self.list_include.topLevelItem(0) )

    def on_btn_include_file_add_clicked( self ):
        for path in qt4tools.getOpenFileNames(self, _('Include file')):
            if len( path ) == 0 :
                continue

            if os.path.islink(path) \
              and not (self.cb_copy_unsafe_links.isChecked() \
              or self.cb_copy_links.isChecked()):
                if self.question_handler( \
                  _('"%s" is a symlink. The linked target will not be backed up until you include it, too.\nWould you like to include the symlinks target instead?') % path ):
                    path = os.path.realpath(path)

            path = self.config.prepare_path( path )

            for index in range( self.list_include.topLevelItemCount() ):
                if path == self.list_include.topLevelItem( index ).text( 0 ):
                    continue

            self.add_include( ( path, 1 ) )

    def on_btn_include_add_clicked( self ):
        for path in qt4tools.getExistingDirectories(self, _('Include folder')):
            if len( path ) == 0 :
                continue

            if os.path.islink(path) \
              and not (self.cb_copy_unsafe_links.isChecked() \
              or self.cb_copy_links.isChecked()):
                if self.question_handler( \
                  _('"%s" is a symlink. The linked target will not be backed up until you include it, too.\nWould you like to include the symlinks target instead?') % path ):
                    path = os.path.realpath(path)

            path = self.config.prepare_path( path )

            for index in range( self.list_include.topLevelItemCount() ):
                if path == self.list_include.topLevelItem( index ).text( 0 ):
                    continue

            self.add_include( ( path, 0 ) )

    def on_btn_snapshots_path_clicked( self ):
        old_path = self.edit_snapshots_path.text()

        path = str(qt4tools.getExistingDirectory(self,
                                                 _('Where to save snapshots'),
                                                 self.edit_snapshots_path.text() ) )
        if len( path ) > 0 :
            if len( old_path ) > 0 and old_path != path:
                if not self.question_handler( _('Are you sure you want to change snapshots folder ?') ):
                    return
            self.edit_snapshots_path.setText( self.config.prepare_path( path ) )

    def on_btn_ssh_private_key_file_clicked( self ):
        old_file = self.txt_ssh_private_key_file.text()

        if not old_file.isEmpty():
            start_dir = self.txt_ssh_private_key_file.text()
        else:
            start_dir = self.config.get_ssh_private_key_folder()
        file = qt4tools.getOpenFileName(self, _('SSH private key'), start_dir)
        if not file.isEmpty():
            self.txt_ssh_private_key_file.setText(file)
        
    def on_combo_modes_changed(self, *params):
        if len(params) == 0:
            index = self.combo_modes.currentIndex()
        else:
            index = params[0]
        active_mode = str( self.combo_modes.itemData( index ) )
        if active_mode != self.mode:
            for mode in list(self.config.SNAPSHOT_MODES.keys()):
                getattr(self, 'mode_%s' % mode).hide()
            for mode in list(self.config.SNAPSHOT_MODES.keys()):
                if active_mode == mode:
                    getattr(self, 'mode_%s' % mode).show()
            self.mode = active_mode
            
        if self.config.mode_need_password(active_mode):
            self.lbl_password_1.setText( self.config.SNAPSHOT_MODES[active_mode][2] + ':' )
            self.frame_password_1.show()
            if self.config.mode_need_password(active_mode, 2):
                self.lbl_password_2.setText( self.config.SNAPSHOT_MODES[active_mode][3] + ':' )
                self.lbl_password_2.show()
                self.txt_password_2.show()
                qt4tools.equal_indent(self.lbl_password_1, self.lbl_password_2)
            else:
                self.lbl_password_2.hide()
                self.txt_password_2.hide()
                qt4tools.equal_indent(self.lbl_password_1)
        else:
            self.frame_password_1.hide()
            
        if active_mode == 'ssh_encfs':
            self.lbl_ssh_encfs_exclude_warning.show()
        else:
            self.lbl_ssh_encfs_exclude_warning.hide()
            
        enabled = active_mode in ('ssh', 'ssh_encfs')
        self.cb_run_nice_on_remote.setEnabled(enabled)
        self.cb_run_ionice_on_remote.setEnabled(enabled)
        self.cb_bwlimit.setEnabled(enabled)
        self.sb_bwlimit.setEnabled(enabled)
            
    def accept( self ):
        if self.validate():
            QDialog.accept( self )

