"""
models.py — SQLite database models for AI English Coach.
Stores all user progress, chat history, quiz results, achievements.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class UserProfile(models.Model):
    LEVELS = [('Beginner','Beginner'),('Elementary','Elementary'),('Intermediate','Intermediate'),('Advanced','Advanced'),('Expert','Expert')]
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='coach_profile'
)
    level           = models.CharField(max_length=20, choices=LEVELS, default='Beginner')
    total_xp        = models.IntegerField(default=0)
    current_streak  = models.IntegerField(default=0)
    longest_streak  = models.IntegerField(default=0)
    last_activity   = models.DateField(null=True, blank=True)
    speaking_score  = models.FloatField(default=0)
    grammar_score   = models.FloatField(default=0)
    vocabulary_score= models.FloatField(default=0)
    interview_score = models.FloatField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.user.username} Profile"

    def update_streak(self):
        today = date.today()
        if self.last_activity:
            delta = (today - self.last_activity).days
            if delta == 1:
                self.current_streak += 1
                if self.current_streak > self.longest_streak:
                    self.longest_streak = self.current_streak
            elif delta > 1:
                self.current_streak = 1
        else:
            self.current_streak = 1
        self.last_activity = today
        self.save()

    def get_level_from_xp(self):
        xp = self.total_xp
        if xp < 500: return 'Beginner'
        elif xp < 1500: return 'Elementary'
        elif xp < 3000: return 'Intermediate'
        elif xp < 6000: return 'Advanced'
        return 'Expert'


class ChatSession(models.Model):
    TYPES = [('text','Text'),('voice','Voice'),('grammar','Grammar'),('speaking','Speaking'),('interview','Interview')]
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_type = models.CharField(max_length=20, choices=TYPES, default='text')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.user.username} - {self.session_type}"


class ChatMessage(models.Model):
    session   = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role      = models.CharField(max_length=10, choices=[('user','User'),('assistant','Assistant')])
    content   = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['timestamp']


class DailyActivity(models.Model):
    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    date               = models.DateField(default=date.today)
    xp_earned          = models.IntegerField(default=0)
    messages_sent      = models.IntegerField(default=0)
    minutes_practiced  = models.IntegerField(default=0)
    grammar_checks     = models.IntegerField(default=0)
    vocab_lookups      = models.IntegerField(default=0)
    speaking_sessions  = models.IntegerField(default=0)
    class Meta: unique_together = ['user', 'date']; ordering = ['-date']


class QuizResult(models.Model):
    TYPES = [('grammar','Grammar'),('vocabulary','Vocabulary'),('speaking','Speaking'),('pronunciation','Pronunciation')]
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    quiz_type       = models.CharField(max_length=20, choices=TYPES)
    score           = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=5)
    correct_answers = models.IntegerField(default=0)
    completed_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.user.username} - {self.quiz_type} - {self.score}%"


class Achievement(models.Model):
    BADGES = [
        ('first_chat','🗨️ First Chat'),('streak_7','🔥 7-Day Streak'),('streak_30','⚡ 30-Day Streak'),
        ('grammar_master','📚 Grammar Master'),('vocab_100','📖 100 Words'),('interview_ace','💼 Interview Ace'),
        ('perfect_score','💯 Perfect Score'),('daily_champ','🏆 Daily Champion'),
    ]
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    badge     = models.CharField(max_length=30, choices=BADGES)
    earned_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ['user', 'badge']


class VocabularyEntry(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vocabulary')
    word         = models.CharField(max_length=100)
    meaning      = models.TextField()
    hindi_meaning= models.CharField(max_length=200, blank=True)
    example      = models.TextField(blank=True)
    saved_at     = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ['user','word']; ordering = ['-saved_at']
