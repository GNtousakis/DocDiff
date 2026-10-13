"""All user-visible strings (Greek). Keep every UI string here for translation."""

APP_NAME = "DocDiff"
WINDOW_TITLE = "DocDiff — Σύγκριση κειμένου από την οθόνη"

PANEL_A_TITLE = "Έγγραφο Α"
PANEL_B_TITLE = "Έγγραφο Β"
PANEL_A_KICKER = "Πρωτότυπο"
PANEL_B_KICKER = "Αναθεώρηση"
APP_SUBTITLE = "Σύγκριση κειμένου από την οθόνη"
DEMO_TAG = "Demo"
THEME_TO_DARK = "Σκοτεινό"
THEME_TO_LIGHT = "Φωτεινό"
WORDS_ONE = "{n} λέξη"
WORDS_MANY = "{n} λέξεις"
CHARS_FMT = "{n} χαρακτήρες"
BTN_CAPTURE = "Λήψη περιοχής"
BTN_ADD_REGION = "Προσθήκη περιοχής"
BTN_COMPARE = "Σύγκριση"
BTN_BACK = "← Επεξεργασία κειμένου"
BTN_SETTINGS = "Ρυθμίσεις"
BTN_REMOVE = "Αφαίρεση"
BTN_CLEAR = "Καθαρισμός"
TEXT_PLACEHOLDER = (
    "Το κείμενο που θα αναγνωριστεί θα εμφανιστεί εδώ.\n"
    "Μπορείτε να το διορθώσετε πριν τη σύγκριση."
)
REGIONS_LABEL = "Περιοχές:"
NO_REGIONS = "Καμία περιοχή"
REGION_PENDING = "Ανάγνωση…"

OVERLAY_HINT = "Σύρετε για να επιλέξετε περιοχή  •  Esc για ακύρωση"

SUMMARY_FMT = "Προσθήκες: {added}   •   Διαγραφές: {removed}   •   Αλλαγές: {changed}"
SUMMARY_IDENTICAL = "Τα κείμενα είναι ίδια."
LEGEND_ADDED = "Προστέθηκε"
LEGEND_REMOVED = "Αφαιρέθηκε"
LEGEND_CHANGED = "Άλλαξε"
LEGEND_REMOVED_ROW = "Διαγραφές"
LEGEND_ADDED_ROW = "Προσθήκες"
LEGEND_CHANGED_ROW = "Αλλαγές"
HINT_ADD_TEXT = "Προσθέστε κείμενο και στα δύο έγγραφα."
BTN_EDIT = "Επεξεργασία"
RESULT_LEFT_TITLE = "Έγγραφο Α"
RESULT_RIGHT_TITLE = "Έγγραφο Β"

SETTINGS_TITLE = "Ρυθμίσεις"
SETTINGS_HOTKEY_A = "Συντόμευση λήψης για το Έγγραφο Α:"
SETTINGS_HOTKEY_B = "Συντόμευση λήψης για το Έγγραφο Β:"
SETTINGS_IGNORE_CASE = "Αγνόηση πεζών/κεφαλαίων"
SETTINGS_IGNORE_PUNCT = "Αγνόηση σημείων στίξης"
SETTINGS_OK = "Αποθήκευση"
SETTINGS_CANCEL = "Ακύρωση"
SETTINGS_HOTKEY_HINT = "Πατήστε τον συνδυασμό πλήκτρων, π.χ. Ctrl+Alt+A"

# Messages / errors
ERR_NO_TEXT = "Δεν βρέθηκε κείμενο στην περιοχή. Δοκιμάστε να επιλέξετε μεγαλύτερη ή πιο καθαρή περιοχή."
ERR_CAPTURE_CANCELLED = "Η λήψη ακυρώθηκε."
ERR_CAPTURE_FAILED = "Η λήψη της οθόνης απέτυχε: {detail}"
ERR_OCR_FAILED = "Η αναγνώριση κειμένου απέτυχε: {detail}"
ERR_OCR_UNAVAILABLE = (
    "Η αναγνώριση κειμένου (OCR) δεν είναι διαθέσιμη σε αυτό το σύστημα. "
    "Η εφαρμογή λειτουργεί σε δοκιμαστική λειτουργία."
)
ERR_OCR_LANG_MISSING = (
    "Η γλώσσα OCR για τα Ελληνικά δεν είναι εγκατεστημένη, οπότε χρησιμοποιούνται οι γλώσσες του "
    "προφίλ σας και τα ελληνικά μπορεί να μην αναγνωρίζονται σωστά.\n\n"
    "Για να την εγκαταστήσετε: Ρυθμίσεις (Settings) > Ώρα και γλώσσα (Time & language) > "
    "Γλώσσα και περιοχή (Language & region) > Προσθήκη γλώσσας (Add a language) > Ελληνικά (Greek). "
    "Βεβαιωθείτε ότι είναι επιλεγμένη η λειτουργία «Οπτική αναγνώριση χαρακτήρων / βασική πληκτρολόγηση» "
    "(Optical character recognition / Basic typing) και επανεκκινήστε την εφαρμογή."
)
ERR_HOTKEY_IN_USE = (
    "Η συντόμευση {hotkey} χρησιμοποιείται ήδη από άλλο πρόγραμμα. "
    "Αλλάξτε την από τις Ρυθμίσεις."
)
ERR_HOTKEY_INVALID = "Μη έγκυρη συντόμευση: {hotkey}. Χρησιμοποιήστε τουλάχιστον ένα πλήκτρο Ctrl/Alt/Shift/Win και ένα γράμμα, αριθμό ή πλήκτρο F."
ERR_HOTKEY_SAME = "Οι δύο συντομεύσεις πρέπει να είναι διαφορετικές."
ERR_HOTKEYS_UNSUPPORTED = "Οι καθολικές συντομεύσεις υποστηρίζονται μόνο στα Windows."
ERR_REMOVE_EDITED = (
    "Το κείμενο αυτής της περιοχής έχει τροποποιηθεί και δεν μπορεί να αφαιρεθεί αυτόματα· "
    "διαγράψτε το χειροκίνητα από το πλαίσιο κειμένου."
)
ERR_COMPARE_EMPTY = "Και τα δύο έγγραφα πρέπει να έχουν κείμενο."

INFO_STUB_MODE = "Δοκιμαστική λειτουργία (χωρίς πραγματικό OCR)."
INFO_CAPTURED = "Η περιοχή καταγράφηκε."
INFO_READING = "Ανάγνωση κειμένου…"
INFO_DONE = "Έτοιμο."
MSG_TITLE_WARNING = "Προειδοποίηση"
MSG_TITLE_ERROR = "Σφάλμα"

# Image comparison mode
MODE_TEXT = "Κείμενο"
MODE_IMAGE = "Εικόνα"
SIMILARITY_CAPTION = "Ομοιότητα"
SIMILARITY_FMT = "{pct}%"
LEGEND_REGIONS = "Περιοχές διαφορών"
SUMMARY_IMAGES_IDENTICAL = "Οι εικόνες είναι ίδιες."
CHK_HEAT = "Θερμικός χάρτης"
IMAGE_PLACEHOLDER = "Η περιοχή που θα καταγραφεί θα εμφανιστεί εδώ."
HINT_ADD_IMAGE = "Καταγράψτε περιοχή και στα δύο έγγραφα."
INFO_COMPARING = "Σύγκριση εικόνων…"
WARN_IMAGE_RESIZED = (
    "Οι εικόνες δεν ευθυγραμμίστηκαν· η Β προσαρμόστηκε στο μέγεθος της Α, "
    "οπότε μικρές μετατοπίσεις μπορεί να εμφανιστούν ως διαφορές."
)
WARN_IMAGE_ASPECT = "Οι εικόνες έχουν διαφορετικές αναλογίες και δεν ευθυγραμμίστηκαν· το ποσοστό είναι ενδεικτικό."
ERR_IMAGE_COMPARE_FAILED = "Η σύγκριση εικόνων απέτυχε: {detail}"
ERR_COMPARE_NO_IMAGE = "Και τα δύο έγγραφα πρέπει να έχουν εικόνα."
SETTINGS_IMAGE_SENSITIVITY = "Ευαισθησία σύγκρισης εικόνων:"
SENSITIVITY_LEVELS = ("Χαμηλή", "Κανονική", "Υψηλή")
