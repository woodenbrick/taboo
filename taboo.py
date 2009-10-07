import gtk
import gtk.glade
import sqlite3
import time
import gobject
import random
import pango
class Game():
    
    def __init__(self):
        self.wTree = gtk.glade.XML("taboo.glade")
        self.conn = sqlite3.Connection("tabooDB")
        self.cursor = self.conn.cursor()
        self.wTree.signal_autoconnect(self)
        self.team_a = []
        self.team_b = []
        #setup cards we will count later but for now grab 500
        max = self.cursor.execute("select max(rowid) from cards").fetchone()[0]
        self.cards = range(1,max+1)
        random.shuffle(self.cards)
    
    def on_name_added(self, entrybox):
        if entrybox.get_text().strip() == "":
            return
        if entrybox.get_text().strip() in self.team_a or entrybox.get_text().strip() in self.team_b:
            self.wTree.get_widget("setup_error").set_text("This user already exists")
            return
        if entrybox.name == "team_a_entry":
            self.team_a.append(entrybox.get_text())
            self.wTree.get_widget("team_a_list").set_markup('<span size="20000">' + "\n".join(self.team_a) + "</span>")
        else:
            self.team_b.append(entrybox.get_text())
            self.wTree.get_widget("team_b_list").set_markup('<span size="20000">' + "\n".join(self.team_b) + "</span>")
        entrybox.set_text("")
        self.wTree.get_widget("setup_error").set_text("")
        
    def on_game_start(self, button):
        if len(self.team_a) < 2 or len(self.team_b) < 2:
            self.wTree.get_widget("setup_error").set_text("Need at least 2 players per team")
            return
        self.num_of_rounds = self.wTree.get_widget("number").get_value()
        self.length_of_rounds = self.wTree.get_widget("length").get_value()
        self.wTree.get_widget("setup").hide()
        self.team_a_turn = 0
        self.team_b_turn = 0
        self.team_a_score = 0
        self.team_b_score = 0
        self.new_round = True
        self.round = 0
        self.time_passed = 0
        self.ten_second_counter = 0
        self.wTree.get_widget("whose_turn").set_markup("""It's <big>%s's</big> turn.""" % self.team_a[self.team_a_turn])
        self.wTree.get_widget("wait_screen").show()


    def on_start_clicked(self, button):
        self.wTree.get_widget("wait_screen").hide()
        self.temp_score = 0
        self.update_timer()
        gobject.timeout_add(1000, self.update_timer)
        self.show_card()
        self.wTree.get_widget("main_screen").show()
        
    def show_card(self):
        self.result = self.cursor.execute("""SELECT word, keyword1, keyword2, keyword3, keyword4,
                                      keyword5 FROM cards WHERE id=?""", (self.cards.pop(),)).fetchone()
        self.wTree.get_widget("card").set_markup("<span size='20000'><u>" + self.result[0] +
                                                 "</u></span>\n\n<span size='15000'>" +
                                                 "\n".join(self.result[1:]) + "</span>")
    
    def next_card(self, button):
        self.ten_second_counter = 0
        if button.name == "success":
            self.temp_score += 1
        elif button.name == "pass":
            self.temp_score -= 1
        else:
            self.cursor.execute("""DELETE FROM cards where word=? and keyword1=? and keyword2=?""",
                                (self.result[0], self.result[1], self.result[2]))
            self.cursor.execute("""INSERT INTO stupidcards (word, keyword1, keyword2) VALUES
                                (?, ?, ?)""", (self.result[0], self.result[1], self.result[2]))
            self.conn.commit()
        if self.new_round:
            self.wTree.get_widget("team_a_score2").set_text(str(self.temp_score + self.team_a_score))
        else:
            self.wTree.get_widget("team_b_score2").set_text(str(self.temp_score + self.team_b_score))
        self.show_card()
        
    def update_timer(self):
        time_since = self.length_of_rounds * 60 - self.time_passed
        self.ten_second_counter += 1
        if time_since == 0:
            self.end_round()
            return False
        time_split = [int(time_since / 60), int(time_since % 60)]
        for i in range(0, 2):
            if time_split[i] == 0:
                time_split[i] = str("00")
            elif time_split[i] <= 9:
                time_split[i] = str("0" + str(time_split[i]))
            else:
                time_split[i] = str(time_split[i])
        self.wTree.get_widget("timer").set_markup("<span size='40000'>" + ":".join(time_split) + "</span>")
        self.time_passed += 1
        return True
    
    def end_round(self):
        penalty = "No penalty as you had less than 10 seconds for this card." if self.ten_second_counter < 11 else ""
        popup = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
        gtk.MESSAGE_INFO, gtk.BUTTONS_YES_NO,
        """Did you get the last card correct? (Word was %s. %s)\n""" % (self.result[0], penalty))
        response = popup.run()
        if response == gtk.RESPONSE_YES:
            self.temp_score += 1
        else:
            if self.ten_second_counter > 10:
                self.temp_score -= 1
        popup.destroy()
        self.new_round = not self.new_round
        if self.new_round:
            self.round += 1
            self.team_b_score += self.temp_score
            score_str = self.score_str(self.team_b[self.team_b_turn])
            self.team_b_turn += 1
            if self.team_b_turn == len(self.team_b):
                self.team_b_turn = 0
            self.wTree.get_widget("whose_turn").set_markup("""%s\nIt's <big>%s's</big> turn.""" % (score_str,self.team_a[self.team_a_turn]))
        else:
            self.team_a_score += self.temp_score
            score_str = self.score_str(self.team_a[self.team_a_turn])
            self.team_a_turn += 1
            if self.team_a_turn == len(self.team_a):
                self.team_a_turn = 0
            self.wTree.get_widget("whose_turn").set_markup("""%s\nIt's <big>%s's</big> turn.""" % (score_str, self.team_b[self.team_b_turn]))
        self.wTree.get_widget("team_a_score").set_text(str(self.team_a_score))
        self.wTree.get_widget("team_b_score").set_text(str(self.team_b_score))
        if self.num_of_rounds != self.round:
            self.time_passed = 0    
        else:
            #game over
            if self.team_a_score == self.team_b_score:
                self.wTree.get_widget("whose_turn").set_text("It was a draw...how disappointing.")
            else:
                if self.team_a_score > self.team_b_score:
                    winners = self.team_a
                else:
                    winners = self.team_b
                self.wTree.get_widget("whose_turn").set_markup("Game Over!\n The winners are:<big>%s</big>" % "\n".join(winners))
            self.wTree.get_widget("go").hide()
            self.wTree.get_widget("wait_quit").show()
            self.wTree.get_widget("new_game").show()
        self.wTree.get_widget("main_screen").hide()
        self.wTree.get_widget("wait_screen").show()        

    def score_str(self, player):
        descriptors = ["dismal", "poor", "lackluster", "decent", "fantastic", "incredible"]
        return "<span size='20000'>%s</span> scored %s %s this round" % (player, self.temp_score,
                                               "point" if self.temp_score == 1 else "points")
            

    def new_game(self, button):
        self.wTree.get_widget("go").show()
        self.wTree.get_widget("wait_quit").hide()
        self.wTree.get_widget("new_game").hide()
        self.wTree.get_widget("wait_screen").hide()
        self.wTree.get_widget("setup").show()
    
    def on_clear_clicked(self, button):
        self.team_a = []
        self.team_b = []
        self.wTree.get_widget("team_b_list").set_text("")
        self.wTree.get_widget("team_a_list").set_text("")
        
    def gtk_main_quit(self, widget):
        self.conn.close()
        gtk.main_quit()
    
Game()
gtk.main()
