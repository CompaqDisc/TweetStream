#!/usr/bin/env python
import curses
import tweepy
import signal
import sys
import textwrap

#Add your own
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

#change this to add hashtags to your view
filters = ['#minecraft','#LILI17']

class StreamListener(tweepy.StreamListener):

    # Set how Twitter should print tweets.
    def _pass_print_method(self, print_method):
        self.printer = print_method

    # What to do when a tweet comes in
    def on_status(self, status):
        self.printer(status.user.name.encode('UTF-8'), status.user.screen_name.encode('UTF-8'), status.text.encode('UTF-8'))
        #print('@{}: {}'.format(status.user.screen_name.encode('UTF-8'), status.text.encode('UTF-8')))

    def on_error(self, status_code):
        if status_code == 420:
            return False
        else:
            print(status_code)


class TwitterAPI:
    
    def __init__(self):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def tweet(self, message):
        self.api.update_status(status=message)
        
    def retweet(self, status_id):
        return self.api.retweet(status_id)
        
    def destroy_status(self, status_id):
        self.api.destroy_status(status_id)

class TweetBoard:
    global running
    running = False
    
    def __init__(self):
        curses.wrapper(self._run)
    
    def pushToTimeline(self, _user, _handle, _body):
        _wbody = textwrap.fill(_body, self.pad_width-2)
        _wbody = '|'.join(('\n'+_wbody).splitlines(True)).lstrip()
        
        #_win.addstr(_user + ' (@'+ _handle + '):\r\n\t' + _body)
        self.window.addstr('\n\n' + _user + ' (@'+ _handle + '):\n' + _wbody)
        
        if self.scroll > 16:
            self.window.refresh(0,0 , 1,max(2,(self.width-self.pad_width)/2) , self.height-4,self.width-max(2,(self.width-self.pad_width)/2))
        elif self.scroll == 2:
            self.window.refresh(self.scroll,0 , 1,max(2,(self.width-self.pad_width)/2) , self.height-4,self.width-max(2,(self.width-self.pad_width)/2))
        else:
            self.window.refresh(self.scroll-5,0 , 1,max(2,(self.width-self.pad_width)/2) , self.height-4,self.width-max(2,(self.width-self.pad_width)/2))
        
        self.scroll += len(_wbody.split('\n')) + 3
        
    def doCMD(self, _cmd, _out, _in):
        if _cmd.lower() == 'help':
            _out.clear()
            _out.addstr(0, 0, 'help: modify the filters variable at the top of the script to suit your needs')
            _out.refresh()
        elif _cmd.lower() == 'quit':
            self._quit(_out, _in)
                
        else:
            _out.clear()
            _out.addstr(0, 0, _cmd.lower() + ': command not found')
            _out.refresh()
    
    def _quit(self, _out, _in):
        _out.clear()
        _out.addstr(0, 0, 'quit: Are you sure? [y/n]')
        _out.refresh()
        if _in.getkey().lower() == 'y':
            _out.clear()
            _out.addstr(0, 0, 'quit: Closing connections... (please wait)')
            _out.refresh()
            _end(-1, -1)
        else:
            _out.clear()
            _out.addstr(0, 0, 'quit: Aborted.')
            _out.refresh()
        _in.clear()
    
    def _run(self, _screen):
        self.scroll = 2
        # Initialize some variables

        # Get some curses init out of the way
        # Get screen size and create menu/status bars
        (height, width) = _screen.getmaxyx()
        statusbar = curses.newwin(1, width, height-2, 0)
        commandbar = curses.newwin(1, width, height-1, 0)
        
        # TimeLine ScrollBack
        # Width of section
        tlsbWidth = min(80, width-4)
        # 1000 Lines of scrollback
        tlsb = curses.newpad(1000, tlsbWidth)
        
        # Set cursor invisible
        curses.curs_set(0)

        # Create some colors and use them
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        
        tlsb.bkgd(' ', curses.color_pair(3))
        statusbar.bkgd(' ', curses.color_pair(2))
        commandbar.bkgd(' ', curses.color_pair(1))
        statusbar.refresh()
        commandbar.refresh()
        
        self.window = tlsb
        self.width = width
        self.height = height
        self.pad_width = tlsbWidth
        
        self.pushToTimeline('CompaqDisc', 'CompaqDisc', 'Thanks for trying out TweetStream, a simple program to manage your Twitter timeline! Type ":help" to learn more!')
        
        #tlsb.refresh(0,0 , 1,max(2,(width-tlsbWidth)/2) , height-4,width-max(2,(width-tlsbWidth)/2))
        
        # Setup background API task.
        # List only those with #devusage in them
        # TODO: User defined filters
        twitter = TwitterAPI()
        tweetStreamListener = StreamListener()
        tweetStreamListener._pass_print_method(self.pushToTimeline)
        tweetStream = tweepy.Stream(auth=twitter.api.auth, listener=tweetStreamListener)
        global filters
        tweetStream.filter(track=filters+['#tweetboardexitfunction'], async=True)

        # Set task as running, wait for interrupt
        # or exit option in UI
        global running
        running = True
        while(running):
            # Is it a command or a function
            inchar = commandbar.getch()
            if inchar == ord(':'):
                # Parse command
                commandbar.addstr(0, 0, ':')
                curses.echo()
                cmd = commandbar.getstr()
                commandbar.clear()
                commandbar.refresh()
                curses.noecho()
                self.doCMD(cmd, statusbar, commandbar)
            else:
                if inchar == ord('q'):
                    self._quit(statusbar, commandbar)
                else:
                    2+2
                    
        # No longer running, tell tweepy to exit background loop on next data.
        tweetStream.disconnect()
        
        # Create some data, because we may not have any availible
        # to close our background task
        dummy = twitter.retweet(852602161422897152)
        twitter.destroy_status(dummy.id)

def _end(signal, frame):
    global running
    running = False

def main():
    signal.signal(signal.SIGINT, _end)
    tb = TweetBoard()

    # Waiting on background thread to exit.

if __name__ == "__main__":
    main()
