import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.gis.geos import Point
from django.utils import timezone


class TripTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time trip tracking"""
    
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.trip_group_name = f'trip_{self.trip_id}'
        
        # Join trip group
        await self.channel_layer.group_add(
            self.trip_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial trip data
        trip_data = await self.get_trip_data()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': trip_data
        }))
    
    async def disconnect(self, close_code):
        # Leave trip group
        await self.channel_layer.group_discard(
            self.trip_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'location_update':
            # Save location and broadcast to group
            await self.handle_location_update(data)
        
        elif message_type == 'stop_arrival':
            # Handle stop arrival
            await self.handle_stop_arrival(data)
        
        elif message_type == 'request_eta':
            # Send ETA update
            await self.send_eta_update(data.get('stop_id'))
    
    async def handle_location_update(self, data):
        """Handle location update from driver"""
        location_data = await self.save_location(data)
        
        # Broadcast to all clients in trip group
        await self.channel_layer.group_send(
            self.trip_group_name,
            {
                'type': 'location_broadcast',
                'location': location_data
            }
        )
    
    async def handle_stop_arrival(self, data):
        """Handle stop arrival notification"""
        arrival_data = await self.save_stop_arrival(data)
        
        # Broadcast to all clients
        await self.channel_layer.group_send(
            self.trip_group_name,
            {
                'type': 'stop_arrival_broadcast',
                'arrival': arrival_data
            }
        )
    
    async def location_broadcast(self, event):
        """Send location update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'data': event['location']
        }))
    
    async def stop_arrival_broadcast(self, event):
        """Send stop arrival to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'stop_arrival',
            'data': event['arrival']
        }))
    
    async def eta_broadcast(self, event):
        """Send ETA update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'eta_update',
            'data': event['eta']
        }))
    
    @database_sync_to_async
    def get_trip_data(self):
        """Get initial trip data"""
        from .models import Trip
        from .serializers import TripDetailSerializer
        
        try:
            trip = Trip.objects.select_related(
                'route', 'driver', 'vehicle'
            ).get(id=self.trip_id)
            
            serializer = TripDetailSerializer(trip)
            return serializer.data
        except Trip.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_location(self, data):
        """Save location log to database"""
        from .models import Trip, LocationLog
        
        try:
            trip = Trip.objects.get(id=self.trip_id)
            
            location = Point(
                float(data.get('lng')),
                float(data.get('lat'))
            )
            
            log = LocationLog.objects.create(
                trip=trip,
                driver=trip.driver,
                location=location,
                speed=data.get('speed'),
                heading=data.get('heading'),
                accuracy=data.get('accuracy'),
                battery_level=data.get('battery_level'),
                timestamp=timezone.now()
            )
            
            return {
                'id': log.id,
                'lat': log.location.y,
                'lng': log.location.x,
                'speed': float(log.speed) if log.speed else 0,
                'heading': float(log.heading) if log.heading else 0,
                'timestamp': log.timestamp.isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    @database_sync_to_async
    def save_stop_arrival(self, data):
        """Save stop arrival to database"""
        from .models import Trip, StopArrival
        from apps.routes.models import RouteStop
        
        try:
            trip = Trip.objects.get(id=self.trip_id)
            stop = RouteStop.objects.get(id=data.get('stop_id'))
            
            location = None
            if data.get('lat') and data.get('lng'):
                location = Point(
                    float(data.get('lng')),
                    float(data.get('lat'))
                )
            
            arrival, created = StopArrival.objects.update_or_create(
                trip=trip,
                stop=stop,
                defaults={
                    'actual_arrival': timezone.now(),
                    'location': location
                }
            )
            
            return {
                'id': arrival.id,
                'stop_id': stop.id,
                'stop_name': stop.stop_name,
                'arrival_time': arrival.actual_arrival.isoformat(),
                'delay_minutes': arrival.delay_minutes
            }
        except Exception as e:
            return {'error': str(e)}
    
    @database_sync_to_async
    def send_eta_update(self, stop_id):
        """Calculate and send ETA update"""
        from .models import Trip
        from apps.routes.models import RouteStop
        from apps.routes.services import ETAService
        
        try:
            trip = Trip.objects.get(id=self.trip_id)
            stop = RouteStop.objects.get(id=stop_id)
            
            eta = ETAService.calculate_eta(trip, stop)
            
            if eta:
                return {
                    'stop_id': stop_id,
                    'eta': eta.isoformat(),
                    'minutes_remaining': (eta - timezone.now()).total_seconds() / 60
                }
            return None
        except Exception as e:
            return {'error': str(e)}


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.user_group_name = f'user_{self.user.id}'
        
        # Join user notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave user group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'mark_read':
            # Mark notification as read
            notification_id = data.get('notification_id')
            await self.mark_notification_read(notification_id)
    
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['notification']
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        from apps.notifications.models import Notification
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False