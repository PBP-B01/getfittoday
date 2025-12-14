from django.db import models
from django.conf import settings

SPORT_CHOICES = [
    ('Aerobics', 'Aerobics'),
    ('Aikido', 'Aikido'),
    ('American Football', 'American Football'),
    ('Archery', 'Archery'),
    ('Arm Wrestling', 'Arm Wrestling'),
    ('Athletics', 'Athletics'),
    ('Badminton', 'Badminton'),
    ('Ballet', 'Ballet'),
    ('Baseball', 'Baseball'),
    ('Basketball', 'Basketball'),
    ('Beach Volleyball', 'Beach Volleyball'),
    ('Billiards', 'Billiards'),
    ('BMX', 'BMX'),
    ('Bodybuilding', 'Bodybuilding'),
    ('Bowling', 'Bowling'),
    ('Boxing', 'Boxing'),
    ('Brazilian Jiu-Jitsu', 'Brazilian Jiu-Jitsu'),
    ('Breakdancing', 'Breakdancing'),
    ('Calisthenics', 'Calisthenics'),
    ('Canoeing', 'Canoeing'),
    ('Capoeira', 'Capoeira'),
    ('Cardio', 'Cardio'),
    ('Cheerleading', 'Cheerleading'),
    ('Chess', 'Chess'),
    ('Climbing', 'Climbing'),
    ('Cricket', 'Cricket'),
    ('CrossFit', 'CrossFit'),
    ('Cycling', 'Cycling'),
    ('Dance', 'Dance'),
    ('Darts', 'Darts'),
    ('Dodgeball', 'Dodgeball'),
    ('Dragon Boat', 'Dragon Boat'),
    ('E-Sports', 'E-Sports'),
    ('Equestrian', 'Equestrian'),
    ('Fencing', 'Fencing'),
    ('Figure Skating', 'Figure Skating'),
    ('Fishing', 'Fishing'),
    ('Floorball', 'Floorball'),
    ('Football', 'Football'),
    ('Frisbee', 'Frisbee'),
    ('Futsal', 'Futsal'),
    ('Golf', 'Golf'),
    ('Gym', 'Gym'),
    ('Gymnastics', 'Gymnastics'),
    ('Handball', 'Handball'),
    ('HIIT', 'HIIT'),
    ('Hiking', 'Hiking'),
    ('Hockey', 'Hockey'),
    ('Horse Riding', 'Horse Riding'),
    ('Ice Skating', 'Ice Skating'),
    ('Jogging', 'Jogging'),
    ('Judo', 'Judo'),
    ('Ju-Jitsu', 'Ju-Jitsu'),
    ('Karate', 'Karate'),
    ('Kayaking', 'Kayaking'),
    ('Kendo', 'Kendo'),
    ('Kickboxing', 'Kickboxing'),
    ('Krav Maga', 'Krav Maga'),
    ('Kung Fu', 'Kung Fu'),
    ('Lacrosse', 'Lacrosse'),
    ('Marathon', 'Marathon'),
    ('Martial Arts', 'Martial Arts'),
    ('Meditation', 'Meditation'),
    ('MMA', 'MMA'),
    ('Motocross', 'Motocross'),
    ('Mountain Biking', 'Mountain Biking'),
    ('Muay Thai', 'Muay Thai'),
    ('Netball', 'Netball'),
    ('Obstacle Racing', 'Obstacle Racing'),
    ('Paddle', 'Paddle'),
    ('Padel', 'Padel'),
    ('Parkour', 'Parkour'),
    ('Pickleball', 'Pickleball'),
    ('Pilates', 'Pilates'),
    ('Ping Pong', 'Ping Pong'),
    ('Pole Dance', 'Pole Dance'),
    ('Polo', 'Polo'),
    ('Powerlifting', 'Powerlifting'),
    ('Rafting', 'Rafting'),
    ('Rock Climbing', 'Rock Climbing'),
    ('Roller Skating', 'Roller Skating'),
    ('Rowing', 'Rowing'),
    ('Rugby', 'Rugby'),
    ('Running', 'Running'),
    ('Sailing', 'Sailing'),
    ('Scuba Diving', 'Scuba Diving'),
    ('Sepak Takraw', 'Sepak Takraw'),
    ('Shooting', 'Shooting'),
    ('Skateboarding', 'Skateboarding'),
    ('Skating', 'Skating'),
    ('Skiing', 'Skiing'),
    ('Slacklining', 'Slacklining'),
    ('Snorkeling', 'Snorkeling'),
    ('Snowboarding', 'Snowboarding'),
    ('Soccer', 'Soccer'),
    ('Softball', 'Softball'),
    ('Spinning', 'Spinning'),
    ('Squash', 'Squash'),
    ('Street Workout', 'Street Workout'),
    ('Surfing', 'Surfing'),
    ('Swimming', 'Swimming'),
    ('Table Tennis', 'Table Tennis'),
    ('Taekwondo', 'Taekwondo'),
    ('Tai Chi', 'Tai Chi'),
    ('Tennis', 'Tennis'),
    ('Track & Field', 'Track & Field'),
    ('Trail Running', 'Trail Running'),
    ('Trampoline', 'Trampoline'),
    ('Triathlon', 'Triathlon'),
    ('TRX', 'TRX'),
    ('Ultimate Frisbee', 'Ultimate Frisbee'),
    ('Volleyball', 'Volleyball'),
    ('Walking', 'Walking'),
    ('Water Polo', 'Water Polo'),
    ('Weightlifting', 'Weightlifting'),
    ('Windsurfing', 'Windsurfing'),
    ('Wrestling', 'Wrestling'),
    ('Wushu', 'Wushu'),
    ('Yoga', 'Yoga'),
    ('Zumba', 'Zumba'),
]

class Community(models.Model):
    name = models.CharField(
        max_length=200, 
        help_text='Name of the sports community'
    )
    short_description = models.CharField(
        max_length=150, 
        blank=True, 
        default="", 
        help_text="Short tagline displayed below the title"
    )
    description = models.TextField(
        help_text='Detailed description of the community'
    )
    contact_info = models.CharField(
        max_length=255, 
        blank=True, 
        help_text='Admin contact info (e.g., Instagram handle, WhatsApp number)'
    )
    schedule = models.TextField(
        blank=True, 
        null=True, 
        help_text="Write schedule separated by new lines. Example: Monday 19:00 - Night Run"
    )
    image = models.ImageField(
        upload_to='community_images/', 
        blank=True, 
        null=True, 
        help_text='Community profile picture'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    fitness_spot = models.ForeignKey(
        'home.FitnessSpot',
        on_delete=models.deletion.CASCADE,
        related_name='communities',
        help_text='Fitness spot where this community usually trains'
    )
    
    category = models.CharField(
        max_length=50, 
        choices=SPORT_CHOICES, 
        help_text='Community category (e.g., Gym, Futsal, Yoga)'
    )
    
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='managed_communities'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='joined_communities'
    )

    class Meta:
        verbose_name = 'Community'
        verbose_name_plural = 'Communities'
        ordering = ['-created_at'] 

    def __str__(self):
        return self.name

    def is_admin(self, user):
        """Check if user is admin of this community"""
        if not user.is_authenticated:
            return False
        return self.admins.filter(id=user.id).exists()
    
    def is_member(self, user):
        """Check if user is member of this community"""
        if not user.is_authenticated:
            return False
        return self.members.filter(id=user.id).exists()

class CommunityPost(models.Model):
    community = models.ForeignKey(Community, on_delete=models.deletion.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} (in {self.community.name})'