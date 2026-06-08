from django.db import models



# Create your models here.
class Category(models.Model):
    name=models.CharField(max_length=20)
    desc=models.TextField(max_length=500)
    image=models.ImageField(upload_to='rani')
    video=models.FileField(upload_to='rachhu')
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Article(models.Model):
    type=models.ForeignKey(Category,on_delete=models.CASCADE,null=True,blank=True)
    title=models.CharField(max_length=20)
    desc=models.TextField(max_length=500)
    author=models.CharField(max_length=30)
    cost=models.IntegerField()
    image=models.ImageField(upload_to='sakshi')
    video=models.FileField(upload_to='dg')
    is_deleted=models.BooleanField(default=False)
    deleted_at=models.DateTimeField(auto_now_add=True,null=True,blank=True)


    def __str__(self):
        return self.title

