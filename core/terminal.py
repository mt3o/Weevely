'''
Created on 22/ago/2011

@author: norby
'''

from core.module import ModuleException
from core.enviroinment import Enviroinment
import readline, atexit, os, re, shlex

module_trigger = ':'
help_string = ':show'
set_string = ':set'
cwd_extract = re.compile( "cd\s+(.+)", re.DOTALL )
respace = re.compile('.*\s+$', re.M)
rcfile = '~/.weevely.rc'
historyfile = '~/.weevely_history'

            
class Terminal(Enviroinment):
    
    def __init__( self, modhandler, one_shot = False):

        self.modhandler = modhandler
        
        
        self.url = modhandler.url
        self.password = modhandler.password
        self.interpreter = modhandler.interpreter

        self.one_shot = one_shot
        
        self.matching_words =  self.modhandler.help_completion('') + [help_string]
    
        self.__load_rcfile(os.path.expanduser( rcfile ))

    
        if not self.interpreter:
            print '[!] [shell.php] No remote backdoor found. Check URL and password.'
    
        elif not one_shot:
            
            Enviroinment.__init__(self)
        
            self.history      = os.path.expanduser( historyfile )

            try:
                readline.set_completer_delims(' \t\n;')
                readline.parse_and_bind( 'tab: complete' )
                readline.set_completer( self.__complete )
                readline.read_history_file( self.history )
                
            except IOError:
                pass
    
            atexit.register( readline.write_history_file, self.history )


    def loop(self):
        
        while self.interpreter:
            
            prompt        = self._format_prompt()
                
            cmd       = raw_input( prompt )
            cmd       = cmd.strip()
            
            if cmd:
                if cmd[0] == module_trigger:
                    self.run_module_cmd(shlex.split(cmd))
                else:
                    self.run_line_cmd(cmd)
            
            
    def run_module_cmd(self, cmd_splitted):
        
        if not self.interpreter:
            return
             
        output = ''
    
        ## Help call
        if cmd_splitted[0] == help_string:
            modname = ''
            if len(cmd_splitted)>1:
                modname = cmd_splitted[1]
            print self.modhandler.helps(modname),
               
        ### Set call
        elif cmd_splitted[0] == set_string:            
            if len(cmd_splitted)>2:
                modname = cmd_splitted[1]
                self.set(modname, cmd_splitted[2:])
               
        else:

        
            if cmd_splitted[0][0] == module_trigger:
                interpreter = cmd_splitted[0][1:]
                cmd_splitted = cmd_splitted[1:]
            else:
                interpreter = self.interpreter
                
            output =  self.run(interpreter, cmd_splitted)
   
        if output != None:
            print output       
            
    def run_line_cmd(self, cmd_line):
        
        if not self.interpreter:
            return
             
        output = ''
        
        if not self.one_shot:

            if self._handleDirectoryChange(cmd_line) == False:
                if self.interpreter == 'shell.php' and cmd_line.startswith('ls'):
                    print self.modhandler.load('shell.php').ls_handler(cmd_line)
                    return
                
                output = self.run(self.interpreter, [ cmd_line ])  
                
            else:
                pass
            
        else:
            output = self.run(self.interpreter, [ cmd_line ])  
            
        if output != None:
            print output
    


    def __complete(self, text, state):
        """Generic readline completion entry point."""
        
        
        
        buffer = readline.get_line_buffer()
        line = readline.get_line_buffer().split()
        
        if ' ' in buffer:
            return []
        
        # show all commands
        if not line:
            return [c + ' ' for c in self.matching_words][state]
        # account for last argument ending in a space
        if respace.match(buffer):
            line.append('')
        # resolve command to the implementation function
        cmd = line[0].strip()
        if cmd in self.matching_words:
            return [cmd + ' '][state]
        results = [c + ' ' for c in self.matching_words if c.startswith(cmd)] + [None]
        if len(results) == 2:
            return results[state].split()[0] + ' '
        return results[state]
        

    def __format_arglist(self, module_arglist):
        
        arguments = {}
        pos = 0
        for arg in module_arglist:
            if '=' in arg:
                name, value = arg.split('=')
            else:
                name = pos
                value = arg
                
            arguments[name] = value
            pos+=1
        
        return arguments


    def set(self, module_name, module_arglist):
        
        if module_name not in self.modhandler.module_info.keys():
            print '[!] Error module with name \'%s\' not found' % (module_name)
        else:
           arguments = self.__format_arglist(module_arglist)
           check, params = self.modhandler.load(module_name).params.set_and_check_parameters(arguments, oneshot=False)
           
           erroutput = ''
           if not check:
               erroutput += 'Error setting parameters. '
               
           print '%sCurrent values: %s' % (erroutput, self.modhandler.load(module_name).params.param_summary())

 
    def run(self, module_name, module_arglist):        
        
        if module_name not in self.modhandler.module_info.keys():
            print '[!] Error module with name \'%s\' not found' % (module_name)
        else:
            arguments = self.__format_arglist(module_arglist)
        
            try:
                response = self.modhandler.load(module_name).run(arguments)
                if response != None:
                    return response
            except KeyboardInterrupt:
                print '[!] Stopped %s execution' % module_name
            except ModuleException, e:
                print '[!] [%s] Error: %s' % (e.module, e.error) 
        
      

    def __load_rcfile(self, path):
        
        if not os.path.exists(path):
            return
        
        try:
            rcfile = open(path, 'r')
        except Exception, e:
            print "[!] Error opening rc file."
            
            
        cmd_list = [c for c in rcfile.read().split('\n') if c and c[0] != '#']
        
        print "[+] Opened rc file with %i commands" % len(cmd_list)
        
        for cmd in cmd_list:
            
            cmd       = cmd.strip()
            
            if cmd:
                print '[+] %s' % (cmd)
                
                if cmd[0] == module_trigger:
                    self.run_module_cmd(shlex.split(cmd))
                else:
                    self.run_line_cmd(cmd)    
    
        
        