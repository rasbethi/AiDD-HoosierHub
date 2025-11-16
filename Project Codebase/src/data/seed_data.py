from src.models.models import db, User, Resource, Booking, Review
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed the database with sample data."""
    
    print("🌱 Starting database seeding...")
    
    # Clear existing data (optional - comment out if you want to keep existing users)
    # db.drop_all()
    # db.create_all()
    
    # ============================================
    # 1. CREATE USERS
    # ============================================
    
    # Admin
    if not User.query.filter_by(email="admin@campushub.edu").first():
        admin = User(
            name="Admin User",
            email="admin@campushub.edu",
            role="admin",
            department="Administration"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        print("✅ Admin user created")
    
    # Staff Members
    staff_list = [
        {"name": "Dr. Sarah Johnson", "email": "sjohnson@faculty.iu.edu", "dept": "Computer Science"},
        {"name": "Prof. Michael Chen", "email": "mchen@faculty.iu.edu", "dept": "Data Science"},
        {"name": "Dr. Emily Rodriguez", "email": "erodriguez@faculty.iu.edu", "dept": "Informatics"},
    ]
    
    for staff_data in staff_list:
        if not User.query.filter_by(email=staff_data["email"]).first():
            staff = User(
                name=staff_data["name"],
                email=staff_data["email"],
                role="staff",
                department=staff_data["dept"]
            )
            staff.set_password("staff123")
            db.session.add(staff)
    
    print("✅ Staff users created")
    
    # Students
    student_list = [
        {"name": "Alex Thompson", "email": "athompson@iu.edu", "dept": "Informatics"},
        {"name": "Priya Patel", "email": "ppatel@iu.edu", "dept": "Data Science"},
        {"name": "James Wilson", "email": "jwilson@iu.edu", "dept": "Computer Science"},
        {"name": "Maria Garcia", "email": "mgarcia@iu.edu", "dept": "Business Analytics"},
        {"name": "David Lee", "email": "dlee@iu.edu", "dept": "Information Systems"},
    ]
    
    for student_data in student_list:
        if not User.query.filter_by(email=student_data["email"]).first():
            student = User(
                name=student_data["name"],
                email=student_data["email"],
                role="student",
                department=student_data["dept"]
            )
            student.set_password("student123")
            db.session.add(student)
    
    print("✅ Student users created")
    
    db.session.commit()
    
    # ============================================
    # 2. CREATE RESOURCES
    # ============================================
    
    # Get users for resource ownership
    staff_users = User.query.filter_by(role="staff").all()
    student_users = User.query.filter_by(role="student").all()
    
    # PUBLIC RESOURCES (Created by students)
    public_resources = [
        {
            "title": "Python Study Group",
            "description": "Weekly Python programming study session. Perfect for beginners and intermediate learners. We cover data structures, algorithms, and real-world projects.",
            "category": "Tutoring",
            "capacity": 15,
            "location": "Luddy Hall, Room 2180",
            "available_slots": 12,
            "access_type": "public",
            "image_url": "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=400&h=300&fit=crop"
        },
        {
            "title": "Data Science Peer Tutoring",
            "description": "Get help with statistics, machine learning, and data visualization. One-on-one or small group sessions available.",
            "category": "Tutoring",
            "capacity": 5,
            "location": "Wells Library, Study Room C",
            "available_slots": 5,
            "access_type": "public",
            "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=300&fit=crop"
        },
        {
            "title": "Collaborative Study Space",
            "description": "Open study area with whiteboards, comfortable seating, and great lighting. Perfect for group projects and exam prep.",
            "category": "Study Room",
            "capacity": 20,
            "location": "Luddy Hall, 3rd Floor Lounge",
            "available_slots": 18,
            "access_type": "public",
            "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=400&h=300&fit=crop"
        },
        {
            "title": "Web Development Workshop",
            "description": "Learn HTML, CSS, JavaScript, and React. Hands-on projects and portfolio building. Every Thursday 6-8 PM.",
            "category": "Tutoring",
            "capacity": 12,
            "location": "Informatics Building, Lab 105",
            "available_slots": 8,
            "access_type": "public",
            "image_url": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=400&h=300&fit=crop"
        },
        {
            "title": "Quiet Study Room A",
            "description": "Silent study space with individual desks, power outlets, and excellent WiFi. No group work allowed.",
            "category": "Study Room",
            "capacity": 10,
            "location": "Wells Library, 4th Floor",
            "available_slots": 7,
            "access_type": "public",
            "image_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop"
        },
    ]
    
    for res_data in public_resources:
        if not Resource.query.filter_by(title=res_data["title"]).first():
            resource = Resource(
                owner_id=random.choice(student_users).id,
                status=Resource.STATUS_PUBLISHED,
                **res_data
            )
            db.session.add(resource)
    
    print("✅ Public resources created")
    
    # RESTRICTED RESOURCES (Created by staff)
    restricted_resources = [
        {
            "title": "AI Research Lab - GPU Cluster",
            "description": "High-performance computing cluster with 8x NVIDIA A100 GPUs. For deep learning research and large-scale ML experiments. Requires lab safety certification.",
            "category": "Lab",
            "capacity": 4,
            "location": "Luddy Hall, Research Wing B201",
            "available_slots": 4,
            "access_type": "restricted",
            "image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&h=300&fit=crop"
        },
        {
            "title": "Molecular Biology Lab Equipment",
            "description": "Centrifuges, microscopes, PCR machines, and gel electrophoresis equipment. Restricted to Biology 400+ courses and approved research projects.",
            "category": "Lab",
            "capacity": 6,
            "location": "Simon Hall, Lab 3012",
            "available_slots": 6,
            "access_type": "restricted",
            "image_url": "https://images.unsplash.com/photo-1582719471384-894fbb16e074?w=400&h=300&fit=crop"
        },
        {
            "title": "Professional Recording Studio",
            "description": "Soundproof studio with industry-standard audio equipment, MIDI controllers, and Adobe Creative Suite. For approved media projects only.",
            "category": "Equipment",
            "capacity": 3,
            "location": "Franklin Hall, Basement Studio",
            "available_slots": 3,
            "access_type": "restricted",
            "image_url": "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=400&h=300&fit=crop"
        },
        {
            "title": "Virtual Reality Development Lab",
            "description": "Meta Quest Pro, HTC Vive Pro, Unity workstations. For XR/VR development courses and approved capstone projects.",
            "category": "Lab",
            "capacity": 8,
            "location": "Informatics Building, Innovation Lab",
            "available_slots": 8,
            "access_type": "restricted",
            "image_url": "https://images.unsplash.com/photo-1617802690658-1173a812650d?w=400&h=300&fit=crop"
        },
        {
            "title": "3D Printing & Fabrication Lab",
            "description": "Ultimaker S5 3D printers, laser cutters, and CNC machines. Safety training required before first use.",
            "category": "Lab",
            "capacity": 5,
            "location": "Luddy Hall, Maker Space",
            "available_slots": 5,
            "access_type": "restricted",
            "image_url": "https://images.unsplash.com/photo-1612815154858-60aa4c59eaa6?w=400&h=300&fit=crop"
        },
        {
            "title": "Portable Projector Kit - Pro",
            "description": "4K projector, portable screen, HDMI cables, and wireless presenter. Perfect for conferences and presentations.",
            "category": "Equipment",
            "capacity": 1,
            "location": "Equipment Checkout Desk, Luddy Hall",
            "available_slots": 1,
            "access_type": "restricted",
            "image_url": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=300&fit=crop"
        },
        {
            "title": "Conference Room with Video Setup",
            "description": "Seats 20 people, 75-inch 4K display, Zoom Rooms setup, wireless screen sharing. For faculty meetings and thesis defenses.",
            "category": "Study Room",
            "capacity": 20,
            "location": "Luddy Hall, 5th Floor Conference",
            "available_slots": 15,
            "access_type": "restricted",
            "image_url": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=400&h=300&fit=crop"
        },
    ]
    
    for res_data in restricted_resources:
        if not Resource.query.filter_by(title=res_data["title"]).first():
            resource = Resource(
                owner_id=random.choice(staff_users).id,
                status=Resource.STATUS_PUBLISHED,
                **res_data
            )
            db.session.add(resource)
    
    print("✅ Restricted resources created")
    
    db.session.commit()
    
    # ============================================
    # 3. CREATE SAMPLE BOOKINGS
    # ============================================
    
    resources = Resource.query.all()[:5]  # Get first 5 resources
    
    for i, resource in enumerate(resources):
        # Create 2-3 bookings per resource
        for j in range(random.randint(2, 3)):
            booking = Booking(
                resource_id=resource.id,
                user_id=random.choice(student_users).id,
                start_time=datetime.now() + timedelta(days=i+1, hours=j*2),
                end_time=datetime.now() + timedelta(days=i+1, hours=j*2+2),
                purpose=f"Need this for my {resource.category.lower()} project",
                status=random.choice(["approved", "pending", "approved"])
            )
            db.session.add(booking)
    
    print("✅ Sample bookings created")
    
    # ============================================
    # 4. CREATE SAMPLE REVIEWS
    # ============================================
    
    approved_bookings = Booking.query.filter_by(status="approved").all()[:5]
    
    review_comments = [
        "Excellent resource! Very well maintained.",
        "Great experience, would definitely book again.",
        "Perfect for what I needed. Highly recommend!",
        "Good resource, but could use better equipment.",
        "Amazing space with all necessary amenities."
    ]
    
    for booking in approved_bookings:
        review = Review(
            resource_id=booking.resource_id,
            reviewer_id=booking.user_id,
            booking_id=booking.id,
            rating=random.randint(4, 5),
            comment=random.choice(review_comments)
        )
        db.session.add(review)
    
    print("✅ Sample reviews created")
    
    db.session.commit()
    
    print("🎉 Database seeding completed successfully!")
    print("\n📝 Login Credentials:")
    print("   Admin: admin@campushub.edu / admin123")
    print("   Staff: sjohnson@faculty.iu.edu / staff123")
    print("   Student: athompson@iu.edu / student123")