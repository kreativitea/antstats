from collections import namedtuple

from utils import open_log
from models import Player
from models import LogLine


def logparser(log):
    ''' Yields a series of events from the log that we care about. 
    Requires an iterator object.
    
    Events that we care about are:
    Round_End
    Round_Start
    <PLAYER> joined team "TERRORIST"
    <PLAYER> joined team "CT"
    <PLAYER> joined team "SPECTATOR"  # meaning they left a team
    <PLAYER> disconnected
    Team <TEAM> triggered "CTs_Win" (CT "1") (T "0")
    Team <TEAM> triggered "Terrorists_Win" (CT "0") (T "1")
    
    '''
    for line in log:
        _, date, _, time, event = line.split(' ', 4)
        
        if is_valid_event(event):
            yield LogLine(date, time.strip(':'), event.strip())


def is_valid_event(event):
    ''' Filter function to check whether or not an event is a valid event. 
    Returns a boolean. '''

    # Team Win event
    if event.startswith("Team") and ("CTs_Win" in event or "Terrorists_Win" in event):
        return True

    # other events
    valid_events = ('disconnected', 'joined team "TERRORIST"', 'joined team "CT"',
                    'joined team "SPECTATOR"', '"Round_Start"', '"Round_End"',
                    'Log file closed')
    return event.strip().endswith(valid_events)


def round_factory(log_name):
    ''' Splits a log into 'rounds'. '''
    log = logparser(open_log(log_name))
    queue = []
    for line in log:
        if line.event in ('World triggered "Round_End"', 'Log file closed'):
            queue.append(line)
            yield queue
            queue = []
        else:
            queue.append(line)


class Rounds(object):
    ''' Yields 'round' information continuously until the log is exhausted.
    
    The round information is consumed by the main whorestats algorithm,
    and modifies information in a database. '''
    def __init__(self, log):
        
        self.rounds = round_factory(log)
        self.te = {}
        self.ct = {}
        self.sp = {}

    def __iter__(self):
        return self

    def next(self):
        while True:
            return self.yield_round()

    def yield_round(self):
        round = self.rounds.next()
        winner = None

        for event in round:
            
            if "CTs_Win" in event.event:
                winner = "CT"
            elif "Terrorists_Win" in event.event:
                winner = "T"

            elif 'joined team "TERRORIST"' in event.event:
                self.change_team(event, self.te)

            elif 'joined team "CT"' in event.event:
                self.change_team(event, self.ct)

            elif 'joined team "SPECTATOR"' in event.event:
                self.change_team(event, self.sp)

            elif 'disconnected' in event.event:
                self.change_team(event, remove=True)

        return {'winner': winner, 
                'te': self.te, 
                'ct': self.ct,
                'sp': self.sp}

    def change_team(self, event, team=None, remove=False):
        player = parse_player(event.event)
        for t in (self.te, self.ct, self.sp):
            try:
                del t[player.steamid]
            except KeyError:
                pass

        if not remove:
            team[player.steamid] = player


def parse_player(pstring):
    ''' Parses a player string.
    
    >>> pstring = "bl00db4th<13><STEAM_0:1:103655><TERRORIST>"
    >>> player, steamid, team = parse_player(pstring)
    >>> print player, steamid, team
    bl00db4th STEAM_0:1:103655 TE
    '''
    pstring = pstring.split('"')[1]
    assert pstring.count('<') >= 3
    assert pstring.count('>') >= 3
    player, i, steamid, team = pstring.rsplit('<', 3)
    return Player(player.rstrip('>'), steamid.rstrip('>'))
