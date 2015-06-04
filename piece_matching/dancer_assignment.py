"""
Script for assigning dancers to pieces based on choreographer and dancer preferences.

author: Karin Tsai (ktsai11@gmail.com)
created: September 2014
"""

PRINTOUT_PATH = 'piece_assignments/'

CHOREO_PREF_FILE = 'CHOREO_SPRING2015.csv'
CHOREO_PREF_HEADERS = ['id', 'name', 'total', 'male', 'female']

DANCER_PREF_FILE = 'DANCER_SPRING_2015.csv'
DANCER_PREF_HEADERS = ['date', 'first', 'last', 'id', 'gender', 'num_pieces']
DANCER_PREF_ENDING_COLUMNS = ['agreement']

SIGN_IN_FILE = 'SIGN_IN_SPRING2015.csv'
SIGN_IN_HEADERS = ['date', 'id', 'last', 'first', 'class_year', 'email',
                   'college', 'semesters', 'phone']

logging = True
verbose = True

class Dancer(object):
    """
    An object representing a dancer and their preferences.

    _id -- unique audition number or identifier of the dancer
    first_name, last_name -- name of dancer
    gender -- dancer's gender ("M" or "F")
    num_pieces -- number of pieces the dancer wishes to be in
    email -- dancer's email
    piece_rankings -- list of piece ids ordered by ranking
    phone -- dancer's phone number
    """
    def __init__(self, _id, first_name, last_name, gender, num_pieces,
                 email, piece_rankings, phone):
        self.id = _id
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.num_pieces = num_pieces
        self.email = email
        self.phone = phone
        self.piece_rankings = piece_rankings
        self.piece_ids = []

    def __str__(self):
        return '%d\t%s\t%s\t%s\t%s' % (self.id,
                                       self.first_name + " " + self.last_name,
                                       self.gender,
                                       self.email,
                                       self.phone)

class Piece(object):
    """
    An object representing a dance piece and its rankings, dancers, and constraints.

    _id -- unique identifier for a piece ("1", Dance A", "Karin's", etc.)
    capacity -- how many dancers should ideally be in this piece
    dancer_rankings -- list of dancer ids ordered by ranking
    gender_constraints -- a list of GenderConstraint objects if applicable
    """
    def __init__(self, _id, name, capacity,
                 dancer_rankings, gender_constraints):
        self.id = _id
        self.name = name
        self.capacity = capacity
        self.gender_constraints = gender_constraints
        self.dancer_rankings = dancer_rankings
        self.dancers = []

    def assign_dancer(self, dancer):
        self.dancers.append(dancer) # assign dancer to piece
        dancer.piece_ids.append(self.id) # assign piece to dancer

    def is_full(self):
        return len(self.dancers) >= self.capacity

    def check_constraints(self, dancer):
        """ Returns true if constraint check passes after adding the given dancer. """
        # number constraints
        if len(dancer.piece_ids) == dancer.num_pieces or self.is_full():
            return False

        # gender constraints
        if not self.gender_constraints:
            return True

        for gc in self.gender_constraints:
            num_gender = len([d for d in self.dancers if d.gender == gc.gender])
            if dancer.gender == gc.gender:
                num_gender += 1
            if num_gender > gc.max:
                return False
        return True

class GenderConstraint(object):
    """
    An object representing a gender constraint on a piece.

    _min -- min number for this gender
    _max -- max number for this gender
    gender -- the gender for which this constraint applies ("M" or "F")
    """
    def __init__(self, _min, _max, gender):
        self.min = _min
        self.max = _max
        self.gender = gender

    def __str__(self):
        return '%d-%d %s' % (self.min, self.max, 'females' if self.gender == 'F' else 'males')

def _csv_to_dancers():
    """
    create map of dancer_id to dancer objects

    NOTE: this does not error check because it assumes error checking already
          happened while running print_audition_sheets.py
    """
    dancer_signin_file = open(SIGN_IN_FILE, 'rU')
    contact_map = {}
    for i, line in enumerate(dancer_signin_file):
        if i == 0: # header line
            continue

        columns = line.strip().split(',')
        _id = int(columns[SIGN_IN_HEADERS.index('id')])
        email = columns[SIGN_IN_HEADERS.index('email')]
        phone = columns[SIGN_IN_HEADERS.index('phone')]
        contact_map[_id] = (email, phone)
    dancer_signin_file.close()

    dancer_ranking_file = open(DANCER_PREF_FILE, 'rU')
    dancer_map = {}
    letter_map = {}
    for i, line in enumerate(dancer_ranking_file):
        columns = line.strip().split(',')
        preferences = columns[len(DANCER_PREF_HEADERS):-len(DANCER_PREF_ENDING_COLUMNS)]

        if i == 0: # header line
            for index, letter in enumerate(preferences):
                letter_map[index+1] = letter
            continue

        _id = int(columns[DANCER_PREF_HEADERS.index('id')])
        first_name = columns[DANCER_PREF_HEADERS.index('first')]
        last_name = columns[DANCER_PREF_HEADERS.index('last')]
        gender = columns[DANCER_PREF_HEADERS.index('gender')]
        num_pieces = int(columns[DANCER_PREF_HEADERS.index('num_pieces')])
        ranking_tuples = [(dance_index, ranking) for dance_index, ranking
                          in enumerate(preferences) if ranking]
        sorted_ranking_tuples = sorted(ranking_tuples,
                                       key=lambda (dance_index, ranking): int(ranking))
        piece_rankings = [dance_index+1 for (dance_index, ranking) in sorted_ranking_tuples]
        (email, phone) = contact_map.get(_id, ('no email', 'no phone'))

        dancer_map[_id] = Dancer(_id, first_name, last_name, gender, num_pieces,
                                 email, piece_rankings, phone)

    dancer_ranking_file.close()
    return (dancer_map, letter_map)

def _csv_to_pieces():
    choreo_ranking_file = open(CHOREO_PREF_FILE, 'rU')
    piece_map = {}
    for i, line in enumerate(choreo_ranking_file):
        if i == 0: # header line
            continue

        columns = line.strip().split(',')
        _id = int(columns[CHOREO_PREF_HEADERS.index('id')])
        name = columns[CHOREO_PREF_HEADERS.index('name')]
        total = int(columns[CHOREO_PREF_HEADERS.index('total')])
        male = int(columns[CHOREO_PREF_HEADERS.index('male')])
        female = int(columns[CHOREO_PREF_HEADERS.index('female')])
        preferences = columns[len(CHOREO_PREF_HEADERS):]
        dancer_rankings = [int(p) for p in preferences if p]

        gender_constraints = []
        if male + female == total:
            gender_constraints.append(GenderConstraint(female, female, 'F'))
            gender_constraints.append(GenderConstraint(male, male, 'M'))

        piece_map[_id] = Piece(_id, name, total, dancer_rankings, gender_constraints)

    choreo_ranking_file.close()
    return piece_map

if __name__ == '__main__':
    (dancers, letter_map) = _csv_to_dancers() # map of dancer id to dancer object
    pieces = _csv_to_pieces() # list of pieces

    if logging:
        log = open('log.txt', 'w+')

    if verbose:
        verbose_log = open('verbose_log.txt', 'w+')

    # TODO: integrity checks
    # print 'Conducting integrity checks...'
    # check top preferences vs genders
    # check multiple rankings

    # create map of top piece choices for dancers
    print 'Initializing top preference map...'
    top_dancer_prefs = {}
    for dancer_id, dancer in dancers.iteritems():
        top_dancer_prefs[dancer_id] = dancer.piece_rankings[:dancer.num_pieces]

    # first, assign all obvious matches (top preferences)
    print 'Calculating first pass (matching top preferences)...'
    for piece_id, piece in pieces.iteritems():
        for i, dancer_id in enumerate(piece.dancer_rankings):
            if i >= piece.capacity:
                break
            if piece_id in top_dancer_prefs.get(dancer_id) and piece_id not in dancer.piece_ids:
                piece.assign_dancer(dancers[dancer_id])
                if piece.is_full():
                    break

    print
    print 'Initial pass results:'
    for piece in pieces.values():
        print '%s (%s, %s) has %d/%d dancers assigned' % (piece.name,
                                                          piece.id,
                                                          letter_map.get(piece.id),
                                                          len(piece.dancers),
                                                          piece.capacity)

    if logging:
        print >> log, '********************'
        print >> log, 'Initial pass results:'
        print >> log, '********************'
        for piece in pieces.values():
            print >> log, '%s (%s, %s):' % (piece.name,
                                            piece.id,
                                            letter_map.get(piece.id))
            for dancer in piece.dancers:
                print >> log, '\t%s %s (%d)' % (dancer.first_name,
                                                dancer.last_name,
                                                dancer.id)

    # now loop through the alternates lists
    print
    print 'Iterating through alternates...'
    pass_number = 1

    if logging:
        print >> log, '\n\n'
        print >> log, '********************'
        print >> log, 'Alternate Assignments:'
        print >> log, '********************'

    done_dancers = set()
    done_pieces = set()

    # tiebreaks
    pieces[3].assign_dancer(dancers[199])
    pieces[17].assign_dancer(dancers[200])
    pieces[16].assign_dancer(dancers[254])
    pieces[19].assign_dancer(dancers[206])

    while pass_number < 1000:
        if logging:
            print >> log, '\nPass %d:' % pass_number
        if verbose:
            print >> verbose_log, '\nPass %d:' % pass_number

        stalemate = True
        for piece_id, piece in pieces.iteritems():
            if verbose:
                print >> verbose_log, ('\n***Checking piece %s (%s, %s)' %
                                       (piece_id, piece.name, letter_map.get(piece_id)))
            if piece_id in done_pieces:
                if verbose:
                    print >> verbose_log, 'Piece is full, continuing'
                continue
            if piece.is_full():
                if verbose:
                    print >> verbose_log, 'Piece added to full list, continuing'
                done_pieces.add(piece.id)
                continue
            dancers_to_consider = [d for d in piece.dancer_rankings
                                   if d not in done_dancers
                                   and d not in [pd.id for pd in piece.dancers]
                                   and piece.id in dancers[d].piece_rankings][:piece.capacity]
            if not dancers_to_consider:
                print >> verbose_log, ('Piece has no more dancers to consider.')
                done_pieces.add(piece_id)
                continue

            dancers_checked = 0
            dancers_to_check = piece.capacity - len(piece.dancers)
            for dancer_id in dancers_to_consider:
                if piece.is_full():
                    continue
                if dancers_to_check == dancers_checked:
                    print >> verbose_log, 'Have to hold on piece.'
                    continue
                dancer = dancers[dancer_id]
                if dancer_id in list(done_dancers) + [d.id for d in piece.dancers]:
                    if verbose:
                        if dancer_id in [d.id for d in piece.dancers]:
                            print >> verbose_log, ('%s %s (%d) is already in the piece' %
                                                   (dancer.first_name, dancer.last_name, dancer.id))
                        elif dancer_id in list(done_dancers):
                            print >> verbose_log, ('%s %s (%d) is already done, not assigned' %
                                                   (dancer.first_name, dancer.last_name, dancer.id))
                    continue  # already in the piece
                if len(dancer.piece_ids) == dancer.num_pieces:
                    done_dancers.add(dancer.id)
                    if verbose:
                        print >> verbose_log, ('%s %s (%d) is already done, not assigned' %
                                               (dancer.first_name, dancer.last_name, dancer.id))
                    continue  # already full on pieces
                remaining_preferences = [r for r in dancer.piece_rankings if
                                         (pieces[r].check_constraints(dancer)
                                          and dancer_id not in [d.id for d in pieces[r].dancers]
                                          and pieces[r] not in done_pieces
                                          and dancer_id in pieces[r].dancer_rankings)]

                if stalemate:
                    not_possible = []
                    for piece_pref in remaining_preferences:
                        preferred_dancers = pieces.get(piece_pref).dancer_rankings
                        next_prefed = 0
                        for pd_id in preferred_dancers:
                            if pd_id == dancer.id:
                                break
                            pd = dancers[pd_id]
                            remaining_prefs = [p for p in pd.piece_rankings if p not in  pd.piece_ids]
                            if remaining_prefs and piece_id == remaining_prefs[0]:
                                next_prefed += 1
                        if next_prefed >= piece.capacity - len(piece.dancers):
                            not_possible.append(piece_pref)
                            continue

                    if not_possible:
                        remaining_preferences =  [p for p in remaining_preferences if p not in not_possible]
                        stalemate = False

                if not remaining_preferences:
                    done_dancers.add(dancer.id)
                    continue
                    if verbose:
                        print >> verbose_log, ('%s %s (%d) has no remaining available preferences' %
                                               (dancer.first_name, dancer.last_name, dancer.id))
                num_pieces_to_consider = dancer.num_pieces - len(dancer.piece_ids)
                pieces_to_consider = remaining_preferences[:num_pieces_to_consider]
                if piece_id in pieces_to_consider:
                    piece.assign_dancer(dancer)
                    if logging:
                        assignment_str = ('%s %s (%d) assigned to %s (%s, %s)' %
                                          (dancer.first_name, dancer.last_name, dancer.id,
                                           piece.name, piece.id, letter_map.get(piece.id)))
                        print >> log, assignment_str

                        if verbose:
                            print >> verbose_log, assignment_str
                elif verbose:
                    considered_pieces_str = '['
                    for i, p_id in enumerate(pieces_to_consider):
                        p = pieces[p_id]
                        if i:
                            considered_pieces_str += ', '
                        considered_pieces_str += '%s (%s, %s)' % (p.name, p.id,
                                                                  letter_map.get(p.id))
                    considered_pieces_str += ']'
                    print >> verbose_log, ('%s %s (%d) not assigned; pieces under consideration: %s' %
                                           (dancer.first_name, dancer.last_name,
                                            dancer.id, considered_pieces_str))
                dancers_checked += 1
        print
        print 'Pass %d results:' % pass_number
        for piece in pieces.values():
            print '%s (%s, %s) has %d/%d dancers assigned' % (piece.name,
                                                              piece.id,
                                                              letter_map.get(piece.id),
                                                              len(piece.dancers),
                                                              piece.capacity)
        pass_number += 1

        if len(done_pieces) == len(pieces):
            break

    print
    print 'Done!'
    print
    print 'Unfilled dances:'
    for p in pieces.values():
        if len(p.dancers) != p.capacity:
            print '%s (%s, %s): %d/%d' % (p.name, p.id, letter_map.get(p.id),
                                          len(p.dancers), p.capacity)

    # print results to files
    for piece in pieces.values():
        f = open(PRINTOUT_PATH + '%s - %s (%s).txt' % (piece.id,
                                                       piece.name.replace('/', '_'),
                                                       letter_map.get(piece.id)), 'w+')
        print >> f, '********************'
        print >> f, '%s (%s, %s)' % (piece.name, piece.id, letter_map.get(piece.id))
        if piece.gender_constraints:
            gender_constraint_string = ', '.join([str(gc) for gc in piece.gender_constraints])
        else:
            gender_constraint_string = 'no gender constraints'
        print >> f, 'Desired: %d dancers (%s)' % (piece.capacity, gender_constraint_string)
        print >> f, 'Matched: %d dancers (%d female, %d male)' % (len(piece.dancers),
                                                                  len([d for d in piece.dancers
                                                                       if d.gender == 'F']),
                                                                  len([d for d in piece.dancers
                                                                       if d.gender == 'M']))
        sorted_dancers = sorted(piece.dancers, key=lambda d: d.id)
        for dancer in sorted_dancers:
            print >> f, dancer
        print >> f, '********************'
        print >> f, 'Emails to copy:'
        print >> f, ', '.join([d.email for d in piece.dancers])

        f.close()

    f = open(PRINTOUT_PATH + 'unassigned.txt', 'w+')
    for dancer in dancers.values():
        if not dancer.piece_ids and dancer.num_pieces:
            print >> f, '%d\t%s\t%s\t%s\t%s' % (dancer.id,
                                                dancer.first_name + " " + dancer.last_name,
                                                dancer.gender,
                                                dancer.email,
                                                dancer.phone)
    f.close()

    if logging:
        log.close()
