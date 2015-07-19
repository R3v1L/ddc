# -*- coding: utf-8 -*-
###############################################################################
# Author: (C) Oliver Gutiérrez
# Module: ddclib
# Description: Django Development Console library module
###############################################################################
# FIXME: Refresh information on apps and models

# FIXME: Collect static command
# FIXME: Text scaping problems
# TODO: Create a file tree widget with folder-file ordering options and context menus, expanding at double clicking, callback at double click on file, etc. 
# TODO: Catch all kind of error if loading an existing project
# TODO: Button for manual information reload (project tree, users, apps, etc)
# TODO: Monitoring for changes (project tree, users, apps, etc)
# TODO: Add editor support?
# TODO: Tasks list?
# TODO: Users editing
# TODO: Database table management (Show, edit, remove registers in a model)
# TODO: Model menu and information
# TODO: Model code generation
# TODO: URL list

# Python imports
from gettext import lgettext as _
import sys,os,pexpect,re,subprocess

# GTK imports
import gobject,gtk

# EVOGTK Imports
import evogtk
from evogtk.gui.guiclass import GUIClass
from evogtk.widgets import TrayIcon,AppIndicator
from evogtk.factories.treeviews import TreeViewFactory
from evogtk.gui import threadtasks
from evogtk.tools import newTextTag,generateSourceWidget,openWithDefaultApp

PYTHONPATH_ORIG=sys.path

class ConsoleOutputRedirector(object):
    """
    Console output redirector to a buffer
    """
    def __init__(self,textview,remove_scaping=False):
        """
        Class initialization
        """
        self.remove_scaping=remove_scaping
        self.re_ctrlchar=re.compile("\033\[[0-9;]*m")
        self.textview=textview
        self.buffer=textview.get_buffer()
        self.accbuf = []

    def update_buffer(self):
        """
        Update buffer data
        """
        text=''.join(self.accbuf)
        if self.remove_scaping:
            text=self.re_ctrlchar.sub('',text)
        self.accbuf = []
        it=self.buffer.get_end_iter()
        self.buffer.place_cursor(it)
        self.buffer.insert(it, text)
        self.textview.scroll_to_mark(self.buffer.get_insert(),0)
        
    def write(self, data):
        """
        Writing method
        """
        self.accbuf.append(data)
        if data.endswith('\n'):
            self.update_buffer()

    def __del__(self):
        """
        Deletion method
        """
        if self.accbuf != []:
            self.update_buffer()

class DjangoProject(object):
    """
    Django project information class
    """
    # TODO: Implement commands in Django Project class: makemessages, compilemessages sqlclear, sqlall, diffsettings, createsuperuser, changepassword, Reset an app
    # TODO: Implement commands as executions of manage.py script
    def __init__(self,name,port,path,settingsmod):
        """
        Class initialization
        """
        # Set project information
        self.name=name
        self.port=port
        self.path=path
        self.settingsmod=settingsmod
        # Change current working directory to project path
        os.chdir(path)
        # If project dir is not in python path, add it
        if not path in PYTHONPATH_ORIG:
            sys.path=list(PYTHONPATH_ORIG)
            sys.path.insert(0,path)
        # Setup settings module variable
        os.environ['DJANGO_SETTINGS_MODULE'] = settingsmod
        # Load settings module
        self.settings=__import__(settingsmod)
        import django
        self.django=django
        reload(self.settings)
        # Django server instance
        self.django_server_instance=None
        # Load needed django modules
        from django.db.models import get_app, get_models
        self.get_app=get_app
        self.get_models=get_models
        from django.core.management import call_command
        self.call_command=call_command
        from django.core.management.color import no_style
        self.style=no_style()

    def reload_all_data(self):
        reload(self.settings)
        reload(self.django)

    def get_settings(self):
        """
        Get a settings dictionary with all settings values
        """
        settingsdict={}
        for var in dir(self.settings):
            if var.isupper():
                settingsdict[var]=getattr(self.settings,var)
        return settingsdict

    def get_apps(self):
        """
        Get apps and models hierarchy in a dictionary
        """ 
        appsdict={}
        for appmod in getattr(self.settings,'INSTALLED_APPS'):
            appname=appmod.split('.')[-1]
            # Get app models
            print appname
            app = self.get_app(appname)
            models=[]
            for model in self.get_models(app):
                models.append(model.__name__)
            appsdict[appname]=models
        return appsdict

    def get_server_buffer(self):
        """
        Read django development server instance output
        """
        if self.django_server_instance:
            try:
                return self.django_server_instance.read_nonblocking(size=4096,timeout=0.01)
            except pexpect.TIMEOUT:
                pass
            except pexpect.EOF:
                pass
        return None

    def get_users(self):
        """
        Get django users
        """
        from django.contrib.auth.models import User
        return User.objects.all()
    
    def create_user(self,username,password,email=None,active=True,staff=False,superuser=False):
        """
        Add a new user to current django project
        """
        from django.contrib.auth.models import User
        try:
            user = User.objects.create_user(username,email,password)
            user.is_active=active
            user.is_staff=staff
            user.is_superuser=superuser
            user.save()
        except Exception,e:
            return False,e
        return True,None
    
    def change_user_password(self,username,password):
        """
        Change password for given user
        """
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
        except:
            return False
        return True
    
    def get_sql(self,appname):
        """
        Return all SQL statements for given application
        """
        from django.core.management.sql import sql_delete,sql_create,sql_custom,sql_indexes
        from django.db import connections, DEFAULT_DB_ALIAS
        app=self.get_app(appname)
        db=connections[DEFAULT_DB_ALIAS]
        # Tables creation statements
        create='\n'.join(sql_create(app, self.style, db))
        # Custom SQL statements
        custom='\n'.join(sql_custom(app, self.style, db))
        # Index creation statements
        indexes='\n'.join(sql_indexes(app, self.style, db))
        # Delete statements
        delete='\n'.join(sql_delete(app, self.style, db))
        return (create,custom,indexes,delete)

    # General commands
    
    def syncdb(self):
        """
        Execute syncdb command
        """
        #self.call_command('syncdb',interactive=False)
        subprocess.call('python manage.py syncdb',cwd=self.path,shell=True)

    def validate(self):
        """
        Execute verify command
        """
        self.call_command('validate',interactive=False)
        
    def cleanup(self):
        """
        Execute cleanup command
        """
        self.call_command('cleanup',interactive=False)
        
    def sqlflush(self):
        """
        Execute sqlflush command
        """
        self.call_command('sqlflush',interactive=False)
        
    # Application related commands
    def sqlall(self,appname):
        """
        Execute sqlall command
        """
        self.call_command('sqlall',appname,interactive=False)
        
    def sqlclear(self,appname):
        """
        Execute sqlclear command
        """
        self.call_command('sqlclear',appname,interactive=False)

    def resetapp(self,appname):
        """
        Reset application to initial values
        """
        self.reload_all_data()
        
        from django.core.management.sql import sql_delete,sql_all
        from django.db import connections, DEFAULT_DB_ALIAS
        # Remove tables
        for i in sql_delete(self.get_app(appname), self.style, connections[DEFAULT_DB_ALIAS]):
            connections[DEFAULT_DB_ALIAS].cursor().execute(i)
        # Resynchronize database
#        for i in sql_all(self.get_app(appname), self.style, connections[DEFAULT_DB_ALIAS]):
#            connections[DEFAULT_DB_ALIAS].cursor().execute(i)
        self.syncdb()


    def runserver(self):
        """
        Run django development server
        """
        if not self.django_server_instance:
            cmd = 'python manage.py runserver %s' % self.port
            self.django_server_instance=pexpect.spawn(cmd,cwd=self.path)

    def stopserver(self):
        """
        Stop django development server
        """
        if self.django_server_instance:
            while self.django_server_instance.isalive():
                self.django_server_instance.sendcontrol('c')
            self.django_server_instance=None

class EVOGTKApp(GUIClass):
    """
    EVOGTK application class
    """
    # Application metadata
    metadata={
        'APP_NAME': _('DDC'),
        'APP_CODENAME': 'ddc',
        'APP_VERSION': '0.5',
        'APP_DESC': _('Django Development Console'),
        'APP_COPYRIGHT': '(C) Oliver Gutiérrez',
        'APP_WEBSITE': 'http://www.evosistemas.com',
        'APP_PREFERENCES': {
            'general': {
                'workspacedir': ('str',['fcbWorkspaceDir'],''),
                'history': ('list',[],[],','),
                'lastproject': ('str',[],''),
                'openlastproject': ('bool',['chkOpenLast'],False),
            },
            'log': {
                'internalcolor': ('str',['clbInternalMessage'],'#000088'),
                'errorcolor': ('str',['clbErrorMessage'],'#880000'),
            }
        }
    }

    # Application task modes
    TASK_SERVERSTOPPED=1
    TASK_SERVERRUNNING=2
    TASK_ACTIVEPROJECT=3

    TASKS_MODES={
        evogtk.TASK_MODE_INITIAL: {
            'enable': [],
            'disable': ['actStopServer','actStartServer','actRestartServer','actOpenBrowser','actCloseProject','actSyncDB','actValidate','actCleanup','actCreateUser'],
            'show': [],
            'hide': [],
            'activate': [],
            'deactivate': [],
            'callback': None
        },
        TASK_ACTIVEPROJECT: {
            'enable': ['actStartServer','actCloseProject','actSyncDB','actValidate','actCleanup','actCreateUser'],
            'disable': [],
            'show': [],
            'hide': [],
            'activate': [],
            'deactivate': [],
            'callback': None
        },
        TASK_SERVERSTOPPED: {
            'enable': ['actStartServer'],
            'disable': ['actStopServer','actRestartServer','actOpenBrowser'],
            'show': [],
            'hide': [],
            'activate': [],
            'deactivate': [],
            'callback': None
        },
        TASK_SERVERRUNNING: {
            'enable': ['actStopServer','actRestartServer','actOpenBrowser'],
            'disable': ['actStartServer'],
            'show': [],
            'hide': [],
            'activate': [],
            'deactivate': [],
            'callback': None
        },
    }

    # Initial values
    __app_initialized=False
    __command_in_progress=False
    currentproject=None
    filemonitor=None

    def initialize(self):
        """
        GUI initialization method
        """        
        # Redirect all console output to console log
        sys.stdout = sys.stderr = ConsoleOutputRedirector(self.widgets.txtConsoleLog)
                
        if evogtk.HAS_APPINDICATOR:
            # Initialize app indicator
            self.trayicon=AppIndicator('django-development-console',icon='ddc-indicator',attention_icon='ddc-indicator-attention',menu=self.widgets.mnuIndicator,iconpath=self.PIXMAPS_DIR)
        else:            
            # Fallback to tray icon
            self.trayicon=TrayIcon(self.PIXMAPS_DIR + '/ddc-icon.png',self.metadata['APP_NAME'],menu=self.widgets.mnuIndicator)
            self.trayicon.show()
        
        # Setup console log text styles
        self.setup_text_styles()

        # Setup projects history treeview
        self.projectshistory=TreeViewFactory('list', ['str','str','str','str'], [_('Name'),_('Settings mod.'),_('Port'),_('Path')],treeview=self.widgets.tvProjectsHistory)

        # Setup project files treeview
        self.projectfiles=TreeViewFactory('tree', [['int','str','pixbuf','str']], [_('File')],[0,1],treeview=self.widgets.tvProjectFiles)

        # Setup application list treeview
        self.projectapps=TreeViewFactory('tree', ['str'], [_('Applications')],menu=self.widgets.mnuAppProperties,showmenucheck=self.applications_menu_check,treeview=self.widgets.tvProjectApps)
        self.update_projects_history()

        # Setup settings list treeview
        self.projectsettings=TreeViewFactory('list', ['str','str'], [_('Setting'),_('Value')],treeview=self.widgets.tvProjectSettings)

        # Setup user list treeview
        self.projectusers=TreeViewFactory('list', ['str','str','str','str','bool','bool','bool'], [_('Username'),_('eMail'),_('First name'),_('Last name'),_('Active'),_('Staff'),_('Superuser')],treeview=self.widgets.tvProjectUsers)

        # Initialize SQL textview widgets
        for i in ['Create','Custom','Indexes','Delete']:
            view=generateSourceWidget('sql', highlightline=False, editable=False, visiblecursor=False)
            view.show()
            self.widgets.add_widget(view, 'txtSQL%s' % i)
            self.widgets.get_widget('scrSQL%s' % i).add(view)
            
        # Setup initial task mode
        self.set_gui_task(evogtk.TASK_MODE_INITIAL)

        # Application has been initialized
        self.__app_initialized=True

        # Show main window
        self.show_mainwindow(self.widgets.winMain)
        
        # Open last project if needed
        last='ddc_project_definition-' + self.preferences.general.lastproject
        if self.preferences.general.openlastproject and last and self.preferences.has_section(last):
            data=self.preferences.get_section(last)
            self.load_project(self.preferences.general.lastproject, data['port'], data['path'], data['settingsmod'])
            # Change task mode to active project
            self.set_gui_task(self.TASK_ACTIVEPROJECT)

    def unload(self):
        """
        Unload application callback
        """
        if self.currentproject:
            self.currentproject.stopserver()

    #===========================================================================
    # GUI event callbacks
    #===========================================================================
    def quitApplication(self,widget,event=None):
        """
        Application quit callback
        """
        if widget == self.widgets.winMain:
            self.ui.actToggleMainWindow=False
        else:
            if self.dialogs.msgDialog(_('Do you want to exit %s?') % self.metadata['APP_NAME'], 'question'):
                self.savePreferences()
                self.quit()
        return True

    def openProject(self,widget=None):
        """
        Open a django project folder
        """
        # Reset open project dialog information
        self.ui.entProjectName =''
        self.ui.spnServerPort = 8000
        self.ui.fcbProjectPath = self.preferences.general.workspacedir
        self.ui.entSettingsMod = 'settings'
        self.widgets.entProjectName.grab_focus()
        # Show open dialog
        while self.dialogs.openDialog(self.widgets.winOpenProject) == 1:
            # Get project information variables
            name=path=self.ui.entProjectName.strip()
            port= int(self.ui.spnServerPort)
            path=self.ui.fcbProjectPath
            settingsmod=self.ui.entSettingsMod.strip()
            # Check if all needed information is OK
            if not name.replace(' ','').isalnum():
                self.dialogs.msgDialog(_('Project name must be an alphanumeric value'),'error')
            else:
                if name and port and path and settingsmod:
                    # Close current project
                    self.closeProject()
                    self.load_project(name,port,path,settingsmod)
                    # Change task mode to active project
                    self.set_gui_task(self.TASK_ACTIVEPROJECT)
                    # Continue when finished loading
                    break
                else:
                    self.dialogs.msgDialog(_('You must fill all the project information fields'),'error')
        # Hide open dialog
        self.widgets.winOpenProject.hide()

    def closeProject(self,widget=None):
        """
        Close current project
        """
        if self.currentproject:
            if self.dialogs.msgDialog(_('Do you want to close current project?'),'question'):
                # Remove project path from python path
                if self.currentproject.path in sys.path:
                    sys.path.remove(self.currentproject.path)
                # Stop django development server
                self.currentproject.stopserver()
                # Remove current project variable
                self.currentproject=None
                # Clear project information treeviews
                self.projectfiles.clear()
                self.projectapps.clear()
                self.projectusers.clear()
                self.projectsettings.clear()
                # Return to initial task mode
                self.set_gui_task(evogtk.TASK_MODE_INITIAL)
                self.widgets.winMain.set_title(_('Django Development Console'))

    def useHistorySettings(self,widget):
        """
        Use selected history row settings into open project dialog fields
        """
        # Get currently selected row
        if self.projectshistory.selected():
            name,settingsmod,port,path=self.projectshistory.selected()        
            self.ui.entProjectName = name
            self.ui.spnServerPort = int(port)
            self.ui.fcbProjectPath = path
            self.ui.entSettingsMod = settingsmod

    def openHistoryProject(self,widget,path,view_column):
        """
        Load selected history project directly
        """
        # Get currently selected row
        if self.projectshistory.selected():
            name,settingsmod,port,path=self.projectshistory.selected()
            # Close current project
            self.closeProject()
            self.load_project(name,port,path,settingsmod)
            # Change task mode to active project
            self.set_gui_task(self.TASK_ACTIVEPROJECT)
            self.widgets.winOpenProject.hide()

    def startServer(self,widget=None):
        """
        Start django development server
        """
        if self.currentproject:
            self.currentproject.runserver()
            self.set_gui_task(self.TASK_SERVERRUNNING)
            gobject.timeout_add(200,self.console_update_loop,priority=gobject.PRIORITY_LOW)
            self.logmsg(_('Django development server started'))
            
    def stopServer(self,widget=None):
        """
        Stop django development server
        """
        if self.currentproject:
            self.currentproject.stopserver()
            self.set_gui_task(self.TASK_SERVERSTOPPED)
            self.logmsg(_('Django development server stopped'))

    def restartServer(self,widget=None):
        """
        Restart django development server
        """
        self.logmsg(_('Restarting django development server'))
        self.stopServer()
        self.startServer()
    
    def syncDB(self,widget=None):
        """
        Synchronize current project database
        """
        if self.currentproject:
            self.run_background_task(self.currentproject.syncdb,_('Synchronizing database'))
    
    def validateModels(self,widget=None):
        """
        Verify project models
        """
        if self.currentproject:
            self.run_background_task(self.currentproject.validate,_('Validating installed models'))
    
    def cleanUp(self,widget=None):
        """
        Clean up database
        """
        if self.currentproject:
            self.run_background_task(self.currentproject.cleanup,_('Cleaning up database'))
    
    def openProjectFile(self,widget,path,view_column):
        """
        Open a project file
        """
        selected=self.projectfiles.selected()
        if selected:
            if selected[0]==0:
                if not widget.row_expanded(path):
                    widget.expand_row(path,False)
                else:
                    widget.collapse_row(path)
            else:
                print "Opening %s" % selected[1]

    def saveConsoleLog(self,widget=None):
        """
        Save log contents into a file
        """
        filename=self.dialogs.fileSelDialog('save', _('Select file to save log text'))
        if filename[0]:
            buf=self.widgets.txtConsoleLog.get_buffer()
            start,end=buf.get_bounds()
            text=buf.get_text(start, end, include_hidden_chars=False)
            fd=open(filename[0][0],'wb')
            fd.write(text)
            fd.close()
            self.logmsg(_('Log contents saved to "%s"') % filename[0][0])
    
    def clearConsoleLog(self,widget=None):
        """
        Clear console log contents
        """
        logbuffer=self.widgets.txtConsoleLog.get_buffer()
        logbuffer.delete(*logbuffer.get_bounds())

    def toggleMainWindow(self,widget=None):
        """
        Toggle main window visibility
        """
        if self.ui.actToggleMainWindow:
            self.widgets.winMain.show()
        else:
            self.widgets.winMain.hide()
            
    def createUser(self,widget=None):
        """
        Create new user
        """
        if self.currentproject:
            while self.dialogs.openDialog(self.widgets.winCreateUser) == 1:
                username=self.ui.entCreateUserName
                password=self.ui.entCreateUserPassword
                passwordconfirm=self.ui.entCreateUserPasswordConfirm
                email=self.ui.entCreateUserEmail
                active=self.ui.chkCreateUserActive
                staff=self.ui.chkCreateUserStaff
                superuser=self.ui.chkCreateUserSuperuser    
                if password != passwordconfirm:
                    self.dialogs.msgDialog(_('Specified passwords do not match'), 'error')
                else:
                    result,msg=self.currentproject.create_user(username,password,email,active,staff,superuser)
                    if not result:
                        self.dialogs.msgDialog(str(msg), 'error')
                    else:
                        self.update_users_information()
                        break
            self.widgets.winCreateUser.hide()
    
    def showSQL(self,widget=None):
        """
        Show SQL for selected application
        """
        appname=self.get_selected_project_app()
        if appname:
            self.ui.txtSQLCreate,self.ui.txtSQLCustom,self.ui.txtSQLIndexes,self.ui.txtSQLDelete = self.currentproject.get_sql(appname)
            self.dialogs.openDialog(self.widgets.winSQL,close=True)

    def resetApp(self,widget=None):
        """
        Reset selected application
        """
        appname=self.get_selected_project_app()
        if appname:
            if self.dialogs.msgDialog(_('Do you really want to reset application "%s"?') % appname, 'question'):
                self.currentproject.resetapp(appname)
                self.logmsg(_('Application "%s" has been reseted') % appname)

    def appProperties(self,widget=None):
        """
        # TODO: Show application properties
        """
        appname=self.get_selected_project_app()
        if appname:
            self.dialogs.msgDialog(_('Application name: %s') % appname, 'info')

    def removeFromHistory(self,widget=None):
        """
        Remove selected project from history list
        """
        if self.projectshistory.selected():
            name=self.projectshistory.selected()[0]
            if self.dialogs.msgDialog(_('Do you really want to remove project "%s" from history?') % name, 'question'):
                if self.preferences.has_section('ddc_project_definition-' + name):
                    self.preferences.remove_section('ddc_project_definition-' + name)
                    history=self.preferences.general.history
                    history.remove(name)
                    self.preferences.general.history=history
                    self.preferences.save()
                self.update_projects_history()

    def clearProjectHistory(self,widget=None):
        """
        Remove all projects from history list
        """
        if self.dialogs.msgDialog(_('Are you sure you really want to remove all projects in history?'), 'question'):
            for name in self.preferences.general.history:
                if self.preferences.has_section('ddc_project_definition-' + name):
                    self.preferences.remove_section('ddc_project_definition-' + name)
            self.preferences.general.history=[]
            self.preferences.save()
            self.update_projects_history()

    def openBrowser(self,widget=None):
        """
        Open web browser pointing to django development server
        """
        openWithDefaultApp('http://localhost:%s' % self.currentproject.port)

    #===========================================================================
    # Utility methods
    #===========================================================================
    def new_editor_tab(self,filename=None):
        """
        Open a new editor tab
        """
        pass

    def applications_menu_check(self,widget,event):
        """
        Applications popup menu checking
        """
        if self.get_selected_project_app():
            return self.widgets.mnuAppProperties
        else:
            # TODO: Create a menu for model properties
            return self.widgets.mnuIndicator

    def get_selected_project_app(self):
        """
        Get treeview selected project application name
        """
        if self.currentproject:
            appname=self.projectapps.selected()
            if appname and appname[0] in self.currentproject.get_apps():
                return appname[0]
        else:
            return None

    def setup_text_styles(self):
        """
        Setup text styles used in application console log
        """
        buf=self.widgets.txtConsoleLog.get_buffer()
        #newTextTag({'name': 'normal','foreground': self.preferences.log.normalcolor},buf)
        newTextTag({'name': 'internal','foreground': self.preferences.log.internalcolor, 'weight': 700},buf)
        #newTextTag({'name': 'info','foreground': self.preferences.log.notifcolor, 'weight': 700},buf)
        newTextTag({'name': 'error','foreground': self.preferences.log.errorcolor, 'weight': 700},buf)

    def logmsg(self,msg,tag='internal'):
        """
        Log a message to console
        """
        logbuffer=self.widgets.txtConsoleLog.get_buffer()
        it=logbuffer.get_end_iter()
        logbuffer.place_cursor(it)
        logbuffer.insert_with_tags_by_name(it,msg + '\n', tag)
        self.widgets.txtConsoleLog.scroll_to_mark(logbuffer.get_insert(),0)
        # Tray icon blinking
        self.trayicon.blink()
        self.notifsys.queue_msg(msg=msg,icon=self.PIXMAPS_DIR + '/ddc-icon.png')
    
    def console_update_loop(self):
        """
        Console update loop
        """
        # Django server monitoring
        if self.currentproject and self.currentproject.django_server_instance and self.currentproject.django_server_instance.isalive():
            bufdata=self.currentproject.get_server_buffer()
            if bufdata:
                print bufdata 
            return self.currentproject.django_server_instance.isalive()
        elif self.currentproject and self.currentproject.django_server_instance and not self.currentproject.django_server_instance.isalive():
            self.logmsg(_('Django development server has exited unexpectedly'),'error')
            self.currentproject.django_server_instance=None
            self.set_gui_task(self.TASK_SERVERSTOPPED)

    def run_background_task(self,callback,msg,*args,**kwargs):
        """
        Run a background task and shows a progress bar with status
        """
        if self.currentproject:
            if not self.__command_in_progress:
                def task(*args,**kwargs):
                    self.widgets.prgCommand.set_text(msg)
                    self.widgets.prgCommand.show()
                    callback(*args,**kwargs)
                
                def gui(*args,**kwargs):
                    self.widgets.prgCommand.pulse()
                    return self.__command_in_progress
                
                def end(*arg,**kwargs):
                    gobject.timeout_add(500,end2,priority=gobject.PRIORITY_HIGH)
                
                def end2():
                    self.widgets.prgCommand.set_text('')
                    self.widgets.prgCommand.hide()
                    self.__command_in_progress=False
                
                self.__command_in_progress=True
                task=threadtasks.ThreadTask(threadtasks.TYPE_SIMPLE,task,gui,end,gui_delay=100)
                task.start(*args,**kwargs)
            else:
                self.dialogs.msgDialog(_('There is another command in progress'),'error')
    
    def load_project(self,name,port,path,settingsmod):
        """
        Load a project
        """
        if not self.currentproject:
            try:
                # Create new django project instance
                self.currentproject=DjangoProject(name,port,path,settingsmod)
            except Exception,e:
                self.currentproject=None
                self.dialogs.msgDialog(_('Error loading project'),'error',str(e))
                return
            # Update files information
            self.update_project_files()
            # Update applications information
            self.update_apps_information()
            # Update users information
            self.update_users_information()
            # Update settings information
            self.update_settings_information()
            # Add project to project history
            history=self.preferences.general.history
            if self.ui.chkAddToHistory and name not in history:
                # Create new config section for new project
                self.preferences.add_section('ddc_project_definition-' + name,{'port': port,'path': path,'settingsmod': settingsmod})
                # Add project to history list
                history.append(name)
                self.preferences.general.history=history
            # Set window title
            self.widgets.winMain.set_title(_('Django Development Console') + ' - '  + name)
            # Add project as last opened one
            self.preferences.general.lastproject = name
            # Save preferences
            self.preferences.save()
            # Update projects history
            self.update_projects_history()

#            # Setup a file monitor for project path
#            if self.filemonitor:
#                del self.filemonitor
#            gfile = gio.File(path)
#            self.filemonitor = gfile.monitor_directory(gio.FILE_MONITOR_NONE, None)
#            self.filemonitor.set_rate_limit(4000)
#            self.filemonitor.connect('changed', self.update_project_files)
            
    def update_apps_information(self):
        """
        Update current project applications information
        """
        try:
            if self.currentproject:
                # Clear treeview
                self.projectapps.clear()
                # Load apps information
                apps=self.currentproject.get_apps()
                for app in apps:
                    iter=self.projectapps.append([app])
                    for model in apps[app]:
                        self.projectapps.append([model],iter)
        except Exception, e:
            self.dialogs.msgDialog(_('Error updating applications data'), 'error', str(e))

    def update_users_information(self):
        """
        Update current project users information
        """
        try:
            if self.currentproject:
                # Clear treeview
                self.projectusers.clear()
                # Load settings information
                users=self.currentproject.get_users()
                for user in users:
                    self.projectusers.append([user.username,user.email,user.first_name,user.last_name,user.is_active,user.is_staff,user.is_superuser])
        except Exception, e:
            self.dialogs.msgDialog(_('Error updating users data'), 'error', str(e))
            
    def update_settings_information(self):
        """
        Update current project settings information
        """
        try:
            if self.currentproject:
                # Clear treeview
                self.projectsettings.clear()
                # Load settings information
                settings=self.currentproject.get_settings()
                for setting in settings:
                    self.projectsettings.append([setting,settings[setting]])
        except Exception, e:
            self.dialogs.msgDialog(_('Error updating settings data'), 'error', str(e))
            
    def update_project_files(self,*args,**kwargs):
        """
        Update project file tree
        """
        try:
            # TODO: Sort files treeview
            if self.currentproject:
                # Clear treeview
                self.projectfiles.clear()
                parents = {}
                filepixbuf=self.icon_theme.load_icon('text', 16,gtk.ICON_LOOKUP_USE_BUILTIN)
                folderpixbuf=self.icon_theme.load_icon('folder', 16,gtk.ICON_LOOKUP_FORCE_SVG)
                
                for path,dirs,files in os.walk(self.currentproject.path):
                    for subdir in dirs:
                        fullpath=os.path.join(path, subdir)
                        parents[fullpath] = self.projectfiles.append([0,fullpath,folderpixbuf,subdir],parents.get(path, None))
                    for item in files:
                        fullpath=os.path.join(path, item)
                        self.projectfiles.append([1,fullpath,filepixbuf,item],parents.get(path, None))
        except Exception, e:
            self.dialogs.msgDialog(_('Error updating project tree data'), 'error', str(e))

    def update_projects_history(self):
        """
        Update projects history information
        """
        # Clear treeview
        self.projectshistory.clear()
        # Load projects information
        for project in self.preferences.general.history:
            if project:
                try:
                    data=self.preferences.get_section('ddc_project_definition-' + project.strip())
                    self.projectshistory.append([project,data['settingsmod'],data['port'],data['path']])
                except:
                    pass
