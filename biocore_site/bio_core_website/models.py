from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db.models import Index

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        indexes = [
            Index(fields=['name'], name='category_name_idx'),
        ]

    def __str__(self):
        return self.name

class Manufacturer(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"
        indexes = [
            Index(fields=['name'], name='manufacturer_name_idx'),
        ]

    def __str__(self):
        return self.name

class Element(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="elements")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    usage = models.TextField(blank=True, null=True)
    manufacturers = models.ManyToManyField(Manufacturer, blank=True)

    class Meta:
        verbose_name = "Элемент"
        verbose_name_plural = "Элементы"
        indexes = [
            Index(fields=['name', 'category'], name='element_name_category_idx'),
        ]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class CustomUser(AbstractUser):
    GENDER_CHOICES = [('M', 'Мужской'), ('F', 'Женский')]
    
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, default='avatars/default.jpg')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=30, unique=True, validators=[MinLengthValidator(4)], db_index=True)

    class Meta:
        indexes = [
            Index(fields=['username'], name='user_username_idx'),
            Index(fields=['email'], name='user_email_idx'),
        ]

    def __str__(self):
        return self.username

class Vitamin(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    element = models.OneToOneField(Element, on_delete=models.CASCADE, related_name='vitamin_data', null=True, blank=True)
    min_normal = models.FloatField()
    max_normal = models.FloatField()
    unit = models.CharField(max_length=20)
    danger_high_level = models.BooleanField(default=True)
    high_level_message = models.TextField(default="Проконсультируйтесь со специалистом")

    class Meta:
        verbose_name = "Витамин"
        verbose_name_plural = "Витамины"
        indexes = [
            Index(fields=['name'], name='vitamin_name_idx'),
            Index(fields=['min_normal', 'max_normal'], name='vitamin_normal_range_idx'),
        ]

    def __str__(self):
        return self.name

class Consultation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='consultations', db_index=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"
        indexes = [
            Index(fields=['user', 'date'], name='consultation_user_date_idx'),
        ]
        ordering = ['-date']
        get_latest_by = 'date'

    def __str__(self):
        return f"Консультация {self.user.username} от {self.date.strftime('%Y-%m-%d')}"

class VitaminLevel(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='vitamin_levels', db_index=True)
    vitamin = models.ForeignKey(Vitamin, on_delete=models.CASCADE, db_index=True)
    value = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = "Уровень витамина"
        verbose_name_plural = "Уровни витаминов"
        unique_together = ('consultation', 'vitamin')
        indexes = [
            Index(fields=['consultation'], name='vitaminlevel_consultation_idx'),
            Index(fields=['vitamin'], name='vitaminlevel_vitamin_idx'),
        ]

    def __str__(self):
        return f"{self.vitamin.name}: {self.value} {self.vitamin.unit}"

class UserBMI(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bmi_history', db_index=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, db_index=True)
    category = models.CharField(max_length=50)

    class Meta:
        verbose_name = "BMI пользователя"
        verbose_name_plural = "BMI пользователей"
        indexes = [
            Index(fields=['user', 'date'], name='bmi_user_date_idx'),
            Index(fields=['bmi'], name='bmi_value_idx'),
        ]
        ordering = ['-date']
        get_latest_by = 'date'

    def save(self, *args, **kwargs):
        # Вычисляем BMI перед сохранением
        self.bmi = self.calculate_bmi(float(self.weight), float(self.height))
        self.category = self.get_bmi_category(float(self.bmi))
        super().save(*args, **kwargs)
    @classmethod
    def calculate_bmi(cls, weight, height):
        height_m = height / 100
        return weight / (height_m ** 2)

    @classmethod
    def get_bmi_category(cls, bmi):
        if bmi < 18.5:
            return "Недостаточный вес"
        elif 18.5 <= bmi < 25:
            return "Нормальный вес"
        elif 25 <= bmi < 30:
            return "Избыточный вес"
        return "Ожирение"

class PromoVideo(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    video_file = models.FileField(upload_to='promo_videos/')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Рекламный ролик"
        verbose_name_plural = "Рекламные ролики"
        ordering = ['-created_at']