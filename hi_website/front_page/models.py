from django.db import models

class Signature(models.Model):
    """ Someone who signed the manifesto """
    name = models.CharField(max_length=100)
    organisation = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, error_messages={'unique': "This email has already signed the manifesto."})
    signed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """ How a signature is shown, e.g. in the admin site """
        return self.name


class Subscriber(models.Model):
    """ Someone who wants the newsletter """
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Newsletter(models.Model):
    """ One issue of the monthly newsletter: what is going on in Hybrid Intelligence this month.
        Written in the admin site. sent_at stays empty until the issue has been sent to everyone. """
    subject = models.CharField(max_length=200)
    text = models.TextField()                                   # TextField = text of any length, with line breaks
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)       # empty = not sent yet (a draft)

    class Meta:
        ordering = ['-created_at']                              # newest first ("-" means newest to oldest)

    def __str__(self):
        return self.subject


class FaqCategory(models.Model):
    """ A group of FAQ questions, e.g. 'HI and Human Expertise'. Shown as a heading on the FAQ page. """
    title = models.CharField(max_length=200)
    anchor = models.SlugField(unique=True)          # the page address part for jumping to it, e.g. #hi-and-human-expertise
    order = models.PositiveIntegerField(default=0)  # the place on the page: 1 first, 2 second, ...

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'FAQ categories'

    def __str__(self):
        return self.title


class FaqQuestion(models.Model):
    """ One question and its answer. Each question belongs to one category: that's the ForeignKey
        (like Player -> Team in the slides). related_name='questions' lets a category find its
        questions with category.questions.all(). """
    category = models.ForeignKey(FaqCategory, on_delete=models.CASCADE, related_name='questions')
    number = models.PositiveIntegerField()          # the number shown in front of the question (1-80)
    question = models.CharField(max_length=300)
    answer = models.TextField()                     # empty lines separate the paragraphs

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"{self.number}. {self.question}"


class PressArticle(models.Model):
    """ One story about Hybrid Intelligence in the news (the Press page). The link goes to the
        article on the newspaper's own website. Added and edited in the admin site. """
    title = models.CharField(max_length=300)
    outlet = models.CharField(max_length=200, blank=True)       # the newspaper or site, e.g. "DR"
    date = models.DateField()
    excerpt = models.TextField(blank=True)                      # the short summary on the card
    url = models.URLField(max_length=500)                       # the link to the article
    image = models.ImageField(upload_to='press/', blank=True)   # saved in media/press/ (needs Pillow)

    class Meta:
        ordering = ['-date']                                    # newest first

    def __str__(self):
        return self.title


class Publication(models.Model):
    """ One research publication on the Research page. "Read more" links to the full text. """
    title = models.CharField(max_length=300)
    date = models.CharField(max_length=50)          # as written, e.g. "1 May 2026" or "October 2026" (not always a full date)
    excerpt = models.TextField(blank=True)
    authors = models.TextField(blank=True)          # the names, separated by commas
    url = models.URLField(max_length=500)
    order = models.PositiveIntegerField(default=0)  # the place on the page: 1 = first (shown as "Latest")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

    def author_names(self):
        """ The authors as a list of names (the text is split at the commas) """
        return [name.strip() for name in self.authors.split(',') if name.strip()]

    def first_authors(self):
        """ The first 8 names, for the page; the rest are behind "+ N more" """
        return self.author_names()[:8]

    def other_authors(self):
        return self.author_names()[8:]


class ResearchSubmission(models.Model):
    """ Research that a visitor shares with us through the "Share your research" form. """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    title = models.CharField(max_length=300)                 # the publication's title
    link = models.URLField(max_length=500, blank=True)       # where it can be read (optional)
    description = models.TextField()                         # a short description of the work
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.title} ({self.name})"
