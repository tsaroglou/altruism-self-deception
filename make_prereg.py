from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas as pdfcanvas

OUTPUT = '/Users/theodorossaroglou/Documents/GitHub/altruism_self/preregistration_aspredicted.pdf'

W, H = A4
L = 2.4 * cm
R = 2.4 * cm
T = 3.6 * cm   # leave room for header
B = 2.2 * cm

# ── colours ──────────────────────────────────────────────────────────────────
RED   = colors.HexColor('#C8150A')
DARK  = colors.HexColor('#1a1a1a')
MED   = colors.HexColor('#3a3a3a')
LIGHT = colors.HexColor('#888888')
RULE  = colors.HexColor('#cccccc')

# ── header / footer drawn on every page ──────────────────────────────────────
def on_page(cnv, doc):
    cnv.saveState()

    # ── AsPredicted wordmark (top-left) ──────────────────────────────────────
    cnv.setFillColor(RED)
    cnv.setFont('Helvetica-Bold', 11)
    cnv.drawString(L, H - 1.5*cm, '\u2192 ASPREDICTED')

    # ── Wharton block (top-right, plain text stand-in) ────────────────────────
    cnv.setFont('Helvetica-Bold', 6.5)
    cnv.setFillColor(colors.HexColor('#002147'))
    cnv.drawRightString(W - R, H - 1.1*cm, 'WHARTON CREDIBILITY LAB')
    cnv.setFont('Helvetica', 6)
    cnv.setFillColor(LIGHT)
    cnv.drawRightString(W - R, H - 1.55*cm, 'UNIVERSITY OF PENNSYLVANIA')

    # ── horizontal rule under header ─────────────────────────────────────────
    cnv.setStrokeColor(RULE)
    cnv.setLineWidth(0.6)
    cnv.line(L, H - 1.9*cm, W - R, H - 1.9*cm)

    # ── footer ────────────────────────────────────────────────────────────────
    cnv.setFont('Helvetica', 6.8)
    cnv.setFillColor(LIGHT)
    cnv.drawString(L, 1.3*cm, 'Version of AsPredicted Questions: 2.00')
    cnv.drawCentredString(W / 2, 1.3*cm,
                          'Available at  https://aspredicted.org/')

    cnv.restoreState()


# ── document ─────────────────────────────────────────────────────────────────
doc = BaseDocTemplate(
    OUTPUT, pagesize=A4,
    rightMargin=R, leftMargin=L,
    topMargin=T, bottomMargin=B
)
frame = Frame(L, B, W - L - R, H - T - B, id='normal')
doc.addPageTemplates([PageTemplate(id='all', frames=frame, onPage=on_page)])

# ── paragraph styles ─────────────────────────────────────────────────────────
def S(name, **kw):
    defaults = dict(fontName='Helvetica', fontSize=8.8, leading=13.4,
                    textColor=MED, alignment=TA_JUSTIFY, spaceAfter=4)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

title_s  = S('title',  fontSize=12.5, fontName='Helvetica-Bold',
             alignment=TA_CENTER, textColor=DARK, spaceAfter=3, leading=16)
sub_s    = S('sub',    fontSize=8, textColor=LIGHT, alignment=TA_CENTER,
             spaceAfter=10, leading=11)
q_s      = S('q',      fontSize=9, fontName='Helvetica-Bold', textColor=DARK,
             spaceBefore=13, spaceAfter=4, leading=13, alignment=TA_LEFT)
body_s   = S('body')
bold_s   = S('bold',   fontName='Helvetica-Bold', spaceAfter=2)
ind_s    = S('ind',    leftIndent=0.45*cm)
italic_s = S('italic', fontName='Helvetica-Oblique', spaceAfter=2,
             textColor=colors.HexColor('#555555'))
small_s  = S('small',  fontSize=8, textColor=LIGHT, alignment=TA_LEFT,
             spaceAfter=2, leading=11)

def Q(text):
    return Paragraph(text, q_s)

def P(text, style=None):
    return Paragraph(text, style or body_s)

def rule():
    return HRFlowable(width='100%', thickness=0.5, color=RULE,
                      spaceAfter=2, spaceBefore=2)

def section(title, *paragraphs):
    items = [Q(title)]
    for p in paragraphs:
        items.append(p)
    return KeepTogether(items) if len(items) <= 6 else items

# ── story ─────────────────────────────────────────────────────────────────────
story = []

story.append(Paragraph(
    'Altruistic Self-Image and Self-Deception',
    title_s))
story.append(Paragraph(
    'Pre-registration &nbsp;&nbsp;|&nbsp;&nbsp; Vienna Center for Experimental Economics',
    sub_s))
story.append(rule())
story.append(Spacer(1, 0.2*cm))

# ── author line ───────────────────────────────────────────────────────────────
story.append(P(
    '<font name="Helvetica-Bold">Author(s)</font>&nbsp;&nbsp; '
    'This pre-registration is anonymous to enable blind peer-review.',
    S('auth', fontSize=8.3, textColor=LIGHT, alignment=TA_LEFT,
      spaceAfter=10, leading=11)))
story.append(rule())

# ─────────────────────────────────────────────────────────────────────────────
# Q1
# ─────────────────────────────────────────────────────────────────────────────
story += [
    Q('1) Have any data been collected for this study already?'),
    P('No, no data have been collected for this study yet.'),
]

# ─────────────────────────────────────────────────────────────────────────────
# Q2
# ─────────────────────────────────────────────────────────────────────────────
story.append(Q('2) What\'s the main question being asked or hypothesis being tested in this study?'))
story.append(P(
    'This study examines whether concerns about one\'s altruistic self-image give rise to '
    'self-deception in decisions involving charitable giving. Participants complete '
    'allocation rounds, each governed by one of two scenarios. In the '
    '<i>win-win</i> scenario, Action A maximises both the participant\'s and the '
    'charity\'s earnings. In the <i>moral conflict</i> scenario, the action that '
    'maximises the participant\'s earnings (Action A) reduces the charity\'s earnings; '
    'choosing the altruistic action (Action B) costs the participant money but '
    'benefits the charity. The active scenario in each round is determined by the '
    'majority symbol — either O or I — among 49 symbols displayed in a 7\u00d77 grid '
    'for 2 seconds. Participants receive a monetary bonus for correctly identifying the '
    'majority symbol, but their identification report does not affect the active '
    'scenario or the resulting payoffs.'))
story.append(P(
    'The main hypothesis is that participants systematically misidentify the active '
    'scenario more often when the true scenario is the moral conflict scenario than '
    'when it is the win-win scenario — and that the direction and magnitude of this '
    'bias depend on their revealed altruistic preferences. Specifically, we predict a '
    'non-monotonic relationship between altruism and self-deception: participants with '
    'intermediate altruism are expected to exhibit the highest profit-driven '
    'self-deception (over-identifying the win-win scenario), while highly altruistic '
    'participants are expected to show image-driven self-deception in the opposite '
    'direction (over-identifying the moral conflict scenario).'))

# ─────────────────────────────────────────────────────────────────────────────
# Q3
# ─────────────────────────────────────────────────────────────────────────────
story.append(Q('3) Describe the key dependent variable(s) specifying how they will be measured.'))
story.append(P(
    'The primary dependent variable is <b>Mistake</b>: a binary indicator equal to 1 '
    'if the participant\'s reported majority symbol in a given round does not match the '
    'true majority symbol in the grid, and 0 otherwise. This variable is observed at '
    'the trial level.'))
story.append(P(
    'The secondary dependent variable is <b>Net Bias</b>: computed at the individual '
    'level as the participant\'s error rate in moral conflict rounds minus their error '
    'rate in win-win rounds, across the 24 ambiguous main rounds. A positive value '
    'indicates profit-driven self-deception; a negative value indicates image-driven '
    'self-deception.'))
story.append(P(
    'An exploratory dependent variable is <b>Reaction Time</b>: the time elapsed '
    'between the grid disappearing from the screen and the participant\'s symbol '
    'report, used to examine deliberation patterns consistent with self-deception.'))

# ─────────────────────────────────────────────────────────────────────────────
# Q4
# ─────────────────────────────────────────────────────────────────────────────
story.append(Q('4) How many and which conditions will participants be assigned to?'))
story.append(P(
    'This is a within-participant design. All participants complete the same task '
    'sequence; there is no between-participant treatment manipulation. The only '
    'between-participant variation is the random assignment of which symbol (O or I) '
    'denotes the moral conflict scenario.'))
story.append(P(
    'The session consists of 4 practice rounds (with feedback) and 28 main rounds '
    '(for payment). Of the 28 main rounds, 4 are unambiguous: 2 in which the moral '
    'conflict symbol occupies all 49 cells, and 2 in which the win-win symbol occupies '
    'all 49 cells. The remaining 24 main rounds are ambiguous, with signal strengths '
    '(majority minus minority count) of 1, 3, 5, and 7 symbols, balanced across both '
    'symbol orientations with 3 repetitions per level per orientation. The 4 '
    'unambiguous rounds are excluded from the self-deception analysis and used solely '
    'to construct the altruism proxy described below.'))
story.append(P(
    'Participants are classified post-hoc into three altruism groups based on their '
    'action choices in the 2 unambiguous moral conflict rounds:'))
story.append(P('\u2022 &nbsp;<b>Selfish</b> (\u03a6\u00a0=\u00a00/2): '
               'chose Action A in both unambiguous moral conflict rounds.', ind_s))
story.append(P('\u2022 &nbsp;<b>Neutral</b> (\u03a6\u00a0=\u00a01/2): '
               'chose Action B in exactly one of the two unambiguous moral conflict rounds.', ind_s))
story.append(P('\u2022 &nbsp;<b>Altruist</b> (\u03a6\u00a0=\u00a02/2): '
               'chose Action B in both unambiguous moral conflict rounds.', ind_s))

# ─────────────────────────────────────────────────────────────────────────────
# Q5
# ─────────────────────────────────────────────────────────────────────────────
story.append(Q('5) Specify exactly which analyses you will conduct to examine the main question/hypothesis.'))

story.append(P('<b>Primary analysis \u2014 Random Effects Probit Model</b>', bold_s))
story.append(P(
    'We estimate a random effects probit model at the trial level using the 24 '
    'ambiguous main rounds only. The dependent variable is Mistake (binary). '
    'The independent variables are: signal strength S (values 1, 3, 5, 7), a binary '
    'indicator C equal to 1 if the true active scenario is moral conflict and 0 if it '
    'is win-win, group dummies Neutral and Altruist (Selfish is the reference '
    'category), the interaction C\u00d7S, the interactions C\u00d7Neutral and '
    'C\u00d7Altruist, and a participant-level random effect u. The model takes the form:'))
story.append(P(
    'P(Mistake<sub>it</sub>\u00a0=\u00a01)\u00a0=\u00a0\u03a6('
    '\u03b2<sub>0</sub> + \u03b2<sub>1</sub>\u00b7S<sub>t</sub> + '
    '\u03b2<sub>2</sub>\u00b7C<sub>t</sub> + \u03b2<sub>3</sub>\u00b7C<sub>t</sub>\u00b7S<sub>t</sub> + '
    '\u03b2<sub>4</sub>\u00b7Neutral<sub>i</sub> + \u03b2<sub>5</sub>\u00b7Altruist<sub>i</sub> + '
    '\u03b2<sub>6</sub>\u00b7C<sub>t</sub>\u00b7Neutral<sub>i</sub> + '
    '\u03b2<sub>7</sub>\u00b7C<sub>t</sub>\u00b7Altruist<sub>i</sub> + u<sub>i</sub>)',
    S('eq', fontName='Helvetica', fontSize=8.8, leading=14,
      alignment=TA_CENTER, spaceBefore=4, spaceAfter=6, textColor=DARK)))

story.append(P('The model is estimated via maximum likelihood. We conduct the following hypothesis tests:'))

tests = [
    ('<b>H1 \u2014 Self-deception exists (\u03b2<sub>2</sub>\u00a0&gt;\u00a00):</b> '
     'moral conflict rounds generate more identification mistakes than win-win rounds, '
     'pooled across groups. One-sided test, \u03b1\u00a0=\u00a00.05.'),
    ('<b>H2 \u2014 Ambiguity facilitates self-deception (\u03b2<sub>3</sub>\u00a0&gt;\u00a00):</b> '
     'a stronger signal reduces moral conflict mistakes more than win-win mistakes. '
     'One-sided test, \u03b1\u00a0=\u00a00.05.'),
    ('<b>H3a \u2014 Neutral group exhibits profit-driven self-deception '
     '(\u03b2<sub>6</sub>\u00a0&gt;\u00a00):</b> '
     'the neutral group has a larger positive net bias than the selfish group. '
     'One-sided test, \u03b1\u00a0=\u00a00.05.'),
    ('<b>H3b \u2014 Non-monotonicity (\u03b2<sub>7</sub>\u00a0\u2212\u00a0\u03b2<sub>6</sub>\u00a0&lt;\u00a00):'
     '</b> the altruist group\'s moral conflict bias is lower than the neutral group\'s. '
     'One-sided test, \u03b1\u00a0=\u00a00.05.'),
    ('<b>H3c \u2014 Altruist group exhibits image-driven self-deception '
     '(\u03b2<sub>7</sub>\u00a0&lt;\u00a00) [exploratory]:</b> '
     'the altruist group over-identifies the moral conflict scenario. Two-sided test.'),
]
for t in tests:
    story.append(P('\u2022 &nbsp;' + t, ind_s))

story.append(Spacer(1, 0.15*cm))
story.append(P('<b>Secondary analysis \u2014 Aggregate OLS</b>', bold_s))
story.append(P(
    'Individual-level net bias (moral conflict error rate minus win-win error rate '
    'across the 24 ambiguous rounds) is regressed on group dummies with '
    'heteroskedasticity-robust standard errors. Predictive margins and pairwise group '
    'contrasts are reported.'))

story.append(P('<b>Robustness checks</b>', bold_s))
story.append(P(
    'The primary probit model is re-estimated (i)\u00a0with gender and trial order as '
    'additional controls, and (ii)\u00a0excluding participants who failed the '
    'comprehension check on their first attempt.'))

story.append(P('<b>Exploratory \u2014 Reaction Time OLS</b>', bold_s))
story.append(P(
    'Individual-level net reaction time of mistakes \u2014 defined as the mean '
    'reaction time for incorrect moral conflict identifications minus the mean reaction '
    'time for incorrect win-win identifications \u2014 is regressed on group dummies '
    'via OLS with robust standard errors. Profit-driven self-deceivers (selfish and '
    'neutral groups) are expected to take longer to make a mistake toward the win-win '
    'scenario; altruists are expected to take longer to make a mistake toward the '
    'moral conflict scenario.'))

# ─────────────────────────────────────────────────────────────────────────────
# Q6
# ─────────────────────────────────────────────────────────────────────────────
story.append(Q('6) Describe exactly how outliers will be defined and handled, '
               'and your precise rule(s) for excluding observations.'))
story.append(P(
    'Participants who fail the comprehension check twice do not proceed to the main '
    'task; this is enforced by the experimental software. For the analysis, we exclude '
    'participants whose error rate on the 2 unambiguous win-win rounds exceeds 50%, as '
    'this indicates a failure to engage seriously with the identification task. '
    'Participants who do not complete the experiment are excluded entirely.'))
story.append(P(
    'For the reaction time analysis only, individual trials with reaction times below '
    '100\u00a0ms or above the participant\'s mean plus 3 standard deviations are '
    'excluded. These trials are retained in all other analyses.'))

# ─────────────────────────────────────────────────────────────────────────────
# Q7
# ─────────────────────────────────────────────────────────────────────────────
story.append(Q('7) How many observations will be collected or what will determine sample size? '
               'No need to justify decision, but be precise about exactly how the number will be determined.'))
story.append(P(
    'The experiment will be conducted at the Vienna Center for Experimental Economics '
    '(VCEE). We plan to recruit approximately 200 participants across 8 to 9 sessions '
    'of approximately 22 to 24 participants each. Sample size was determined on the '
    'basis of a power analysis targeting the primary hypothesis H3a. Assuming a '
    'small-to-medium effect size (Cohen\'s d\u00a0\u2248\u00a00.25) for a one-sample '
    'test of whether the neutral group\'s mean net bias exceeds zero, and that the '
    'neutral group constitutes approximately 20% of the sample, N\u00a0=\u00a0200 '
    'provides sufficient observations for the trial-level random-effects probit '
    'analysis. We acknowledge that individual-level aggregate tests may be '
    'underpowered, particularly for the neutral group.'))

# ─────────────────────────────────────────────────────────────────────────────
# Q8
# ─────────────────────────────────────────────────────────────────────────────
story.append(Q('8) Anything else you would like to pre-register? '
               '(e.g., secondary analyses, variables collected for exploratory purposes, '
               'unusual analyses planned?)'))

story.append(P('<b>Payoff structure.</b> '
    'Win-win scenario: Action\u00a0A yields \u20ac7 to the participant and \u20ac5 to '
    'the charity; Action\u00a0B yields \u20ac5 to the participant and \u20ac1.50 to '
    'the charity. Moral conflict scenario: Action\u00a0A yields \u20ac7 to the '
    'participant and \u20ac1.50 to the charity; Action\u00a0B yields \u20ac5 to the '
    'participant and \u20ac5 to the charity. The identification bonus is \u20ac1 for '
    'a correct symbol report.'))

story.append(P('<b>Grid and timing.</b> '
    'The grid contains 49 cells arranged in a 7\u00d77 layout. Each grid is displayed '
    'for 2 seconds, preceded by a 3-second fixation cross.'))

story.append(P('<b>Payment.</b> '
    'One of the 28 main rounds is selected at random at the end of the session. The '
    'participant receives the action payoff from that round plus the identification '
    'bonus if they correctly identified the majority symbol. Participants also receive '
    'a show-up fee.'))

story.append(P('<b>Charity.</b> The designated charity is GiveDirectly.'))

story.append(P('<b>Questionnaire.</b> '
    'Following the main task, participants complete a short questionnaire covering age, '
    'gender, education level, employment status, field of study, self-reported '
    'altruism, charitable donation frequency, perceived task difficulty, and an '
    'open-ended question about the study\'s purpose.'))

story.append(P('<b>Significance level.</b> '
    '\u03b1\u00a0=\u00a00.05 for all confirmatory hypothesis tests (H1, H2, H3a, '
    'H3b). H3c is pre-registered as exploratory.'))

story.append(P('<b>Control variables.</b> '
    'The following participant characteristics are collected and used as controls in '
    'the robustness specifications: age, gender, education level, field of study, and '
    'trial order within the session.'))

# ── build ─────────────────────────────────────────────────────────────────────
doc.build(story)
print('Done:', OUTPUT)
