<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Cube extends Model
{
    use HasFactory;

    protected $table = 'cubes';

    protected $fillable = [
        'group_id',
        'color',
        'face',
        'individual_time',
    ];

    public function group()
    {
        return $this->belongsTo(GroupOfThree::class, 'group_id');
    }
}
